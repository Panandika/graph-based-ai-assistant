import re
from collections.abc import Awaitable, Callable, Hashable
from typing import Annotated, Any, TypedDict, cast

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from pymongo import MongoClient

from app.core.config import LLMProvider, get_settings
from app.core.llm import get_llm, validate_model
from app.models.graph import Graph, NodeType
from app.services.llm_transform_service import (
    create_input_image_node,
    create_input_text_node,
    create_llm_transform_node,
)


class AgentState(TypedDict):
    """State container for agent workflow execution."""

    messages: Annotated[list[BaseMessage], add_messages]
    current_node: str
    input_data: dict[str, Any]
    output_data: dict[str, Any]


def get_checkpointer() -> MongoDBSaver:
    """Get MongoDB checkpointer for state persistence."""
    settings = get_settings()
    client: MongoClient[dict[str, Any]] = MongoClient(settings.mongodb_url)
    return MongoDBSaver(client, db_name=settings.database_name)


def interpolate_prompt(template: str, variables: dict[str, Any]) -> str:
    """Replace {{variable}} placeholders with values from variables dict."""

    def replacer(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        return str(variables.get(key, match.group(0)))

    return re.sub(r"\{\{(\w+)\}\}", replacer, template)


def create_llm_node(
    node_config: dict[str, Any],
) -> Callable[[AgentState], Awaitable[dict[str, Any]]]:
    """Factory to create an LLM node function with specific configuration."""
    provider_str = node_config.get("provider", "openai")
    model = node_config.get("model", "gpt-4o-mini")
    prompt_template = node_config.get("prompt", "")

    try:
        provider = LLMProvider(provider_str)
    except ValueError:
        provider = LLMProvider.OPENAI

    if not validate_model(provider, model):
        settings = get_settings()
        model = settings.default_model

    async def llm_node(state: AgentState) -> dict[str, Any]:
        """Process state through LLM with node-specific configuration."""
        llm = get_llm(provider=provider, model=model)
        messages = list(state["messages"])

        if prompt_template:
            interpolated = interpolate_prompt(prompt_template, state["input_data"])
            messages.insert(0, HumanMessage(content=interpolated))

        response = await llm.ainvoke(messages)
        return {
            "messages": [response],
            "output_data": {"response": response.content},
        }

    return llm_node


async def tool_node(state: AgentState) -> dict[str, Any]:
    """Execute a tool based on state."""
    return {
        "output_data": {"tool_result": "Tool executed successfully"},
    }


def create_condition_router(
    condition_config: dict[str, Any],
) -> Callable[[AgentState], str]:
    """Create a conditional router function."""

    def router(state: AgentState) -> str:
        last_message = state["messages"][-1] if state["messages"] else None
        if last_message and isinstance(last_message, AIMessage):
            content = str(last_message.content).lower()
            if "yes" in content or "true" in content:
                return "true"
        return "false"

    return router


class GraphExecutor:
    """Executes a graph configuration as a LangGraph workflow."""

    def __init__(self, graph: Graph):
        self.graph = graph
        self._compiled: CompiledStateGraph[Any] | None = None

    def _build_graph(self) -> StateGraph[AgentState]:
        """Build a LangGraph StateGraph from the graph configuration."""
        builder = StateGraph(AgentState)

        node_map: dict[str, str] = {}

        for node in self.graph.nodes:
            node_id = node.id
            node_type = node.data.node_type

            if node_type == NodeType.START:
                node_map[node_id] = START
            elif node_type == NodeType.END:
                node_map[node_id] = END
            elif node_type == NodeType.LLM:
                llm_fn = create_llm_node(node.data.config)
                builder.add_node(node_id, llm_fn)  # type: ignore[call-overload]
                node_map[node_id] = node_id
            elif node_type == NodeType.LLM_TRANSFORM:
                transform_fn = create_llm_transform_node(node.data.config)
                builder.add_node(node_id, transform_fn)  # type: ignore[call-overload]
                node_map[node_id] = node_id
            elif node_type == NodeType.INPUT_TEXT:
                import asyncio

                input_fn = asyncio.run(create_input_text_node(node.data.config))
                builder.add_node(node_id, input_fn)  # type: ignore[call-overload]
                node_map[node_id] = node_id
            elif node_type == NodeType.INPUT_IMAGE:
                import asyncio

                input_fn = asyncio.run(create_input_image_node(node.data.config))
                builder.add_node(node_id, input_fn)  # type: ignore[call-overload]
                node_map[node_id] = node_id
            elif node_type == NodeType.TOOL:
                builder.add_node(node_id, tool_node)
                node_map[node_id] = node_id
            elif node_type == NodeType.CONDITION:
                node_map[node_id] = node_id

        for edge in self.graph.edges:
            source = node_map.get(edge.source, edge.source)
            target = node_map.get(edge.target, edge.target)

            source_node = next(
                (n for n in self.graph.nodes if n.id == edge.source), None
            )

            if source_node and source_node.data.node_type == NodeType.CONDITION:
                condition_edges = [
                    e for e in self.graph.edges if e.source == edge.source
                ]
                if len(condition_edges) >= 2:
                    path_map: dict[str, str] = {}
                    for ce in condition_edges:
                        ce_target = node_map.get(ce.target, ce.target)
                        if ce.source_handle == "true":
                            path_map["true"] = ce_target
                        else:
                            path_map["false"] = ce_target

                    if path_map and source not in [START, END]:
                        builder.add_conditional_edges(
                            source,
                            create_condition_router(source_node.data.config),
                            cast(dict[Hashable, str], path_map),
                        )
            else:
                if source == START:
                    builder.add_edge(START, target)
                elif target == END:
                    builder.add_edge(source, END)
                elif source not in [START, END] and target not in [START, END]:
                    builder.add_edge(source, target)

        return builder

    def compile(self) -> None:
        """Compile the graph for execution."""
        builder = self._build_graph()
        checkpointer = get_checkpointer()
        self._compiled = builder.compile(checkpointer=checkpointer)

    async def execute(
        self,
        thread_id: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the workflow with the given input."""
        if not self._compiled:
            self.compile()

        assert self._compiled is not None

        initial_state: AgentState = {
            "messages": [HumanMessage(content=str(input_data.get("message", "")))],
            "current_node": "",
            "input_data": input_data,
            "output_data": {},
        }

        config = RunnableConfig(configurable={"thread_id": thread_id})

        result = await self._compiled.ainvoke(initial_state, config)

        return {
            "messages": [
                {
                    "role": "ai" if isinstance(m, AIMessage) else "human",
                    "content": m.content,
                }
                for m in result.get("messages", [])
            ],
            "output_data": result.get("output_data", {}),
        }
