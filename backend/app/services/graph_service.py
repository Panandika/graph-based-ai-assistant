import logging
import re
import time
from collections.abc import Awaitable, Callable, Hashable
from typing import Any, cast

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pymongo import MongoClient

from app.core.config import LLMProvider, get_settings
from app.core.llm import get_llm, validate_model
from app.models.graph import Graph, NodeType
from app.models.state import AgentState
from app.services.canva_node_service import (
    create_canva_mcp_node,
    create_output_export_node,
)
from app.services.llm_transform_service import (
    create_input_image_node,
    create_input_text_node,
    create_llm_transform_node,
    create_output_node,
)

logger = logging.getLogger(__name__)


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
        logger.info(
            f"GraphExecutor initialized with graph: "
            f"name='{graph.name}', nodes={len(graph.nodes)}, edges={len(graph.edges)}"
        )

    def _build_graph(self) -> StateGraph[AgentState]:
        """Build a LangGraph StateGraph from the graph configuration."""
        logger.info("Building LangGraph StateGraph...")
        builder: StateGraph[AgentState] = StateGraph(AgentState)

        node_map: dict[str, str] = {}

        for node in self.graph.nodes:
            node_id = node.id
            node_type = node.data.node_type
            logger.debug(f"Processing node: id='{node_id}', type={node_type.value}")

            if node_type == NodeType.START:
                node_map[node_id] = START
                logger.info(f"  → Mapped START node: {node_id}")
            elif node_type == NodeType.END:
                node_map[node_id] = END
                logger.info(f"  → Mapped END node: {node_id}")
            elif node_type == NodeType.LLM:
                llm_fn = create_llm_node(node.data.config)
                builder.add_node(node_id, llm_fn)  # type: ignore[call-overload]
                node_map[node_id] = node_id
                logger.info(f"  → Added LLM node: {node_id}")
            elif node_type == NodeType.LLM_TRANSFORM:
                transform_fn = create_llm_transform_node(node.data.config)
                builder.add_node(node_id, transform_fn)  # type: ignore[call-overload]
                node_map[node_id] = node_id
                logger.info(f"  → Added LLM_TRANSFORM node: {node_id}")
            elif node_type == NodeType.INPUT_TEXT:
                # Merge value into config so the factory gets the user's input
                merged_config = {**node.data.config}
                if node.data.value:
                    merged_config["value"] = node.data.value
                input_fn = create_input_text_node(merged_config)
                builder.add_node(node_id, input_fn)  # type: ignore[call-overload]
                node_map[node_id] = node_id
                logger.info(f"  → Added INPUT_TEXT node: {node_id}")
            elif node_type == NodeType.INPUT_IMAGE:
                # Merge value into config
                merged_config = {**node.data.config}
                if node.data.value:
                    merged_config["value"] = node.data.value
                input_fn = create_input_image_node(merged_config)
                builder.add_node(node_id, input_fn)  # type: ignore[call-overload]
                node_map[node_id] = node_id
                logger.info(f"  → Added INPUT_IMAGE node: {node_id}")
            elif node_type == NodeType.CANVA_MCP:
                canva_fn = create_canva_mcp_node(node.data.config)
                builder.add_node(node_id, canva_fn)  # type: ignore[call-overload]
                node_map[node_id] = node_id
                logger.info(f"  → Added CANVA_MCP node: {node_id}")
            elif node_type == NodeType.OUTPUT_EXPORT:
                export_fn = create_output_export_node(node.data.config)
                builder.add_node(node_id, export_fn)  # type: ignore[call-overload]
                node_map[node_id] = node_id
                logger.info(f"  → Added OUTPUT_EXPORT node: {node_id}")
            elif node_type == NodeType.TOOL:
                builder.add_node(node_id, tool_node)
                node_map[node_id] = node_id
                logger.info(f"  → Added TOOL node: {node_id}")
            elif node_type == NodeType.CONDITION:
                node_map[node_id] = node_id
                logger.info(f"  → Added CONDITION node: {node_id}")
            elif node_type == NodeType.OUTPUT:
                output_fn = create_output_node(node.data.config)
                builder.add_node(node_id, output_fn)  # type: ignore[arg-type]
                node_map[node_id] = node_id
                logger.info(f"  → Added OUTPUT (collect) node: {node_id}")

        logger.info(f"Adding {len(self.graph.edges)} edges...")
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
                        logger.info(f"  → Added conditional edge from {source}")
            else:
                if source == START:
                    builder.add_edge(START, target)
                    logger.info(f"  → Edge: START → {target}")
                elif target == END:
                    builder.add_edge(source, END)
                    logger.info(f"  → Edge: {source} → END")
                elif source not in [START, END] and target not in [START, END]:
                    builder.add_edge(source, target)
                    logger.info(f"  → Edge: {source} → {target}")

        logger.info("Graph building complete")
        return builder

    def compile(self) -> None:
        """Compile the graph for execution."""
        logger.info("Compiling graph with MongoDB checkpointer...")
        builder = self._build_graph()
        checkpointer = get_checkpointer()
        self._compiled = builder.compile(checkpointer=checkpointer)
        logger.info("Graph compilation complete")

    async def execute(
        self,
        thread_id: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the workflow with the given input."""
        logger.info(f"Executing graph for thread_id={thread_id}")
        logger.info(f"Input data: {input_data}")
        start_time = time.time()

        if not self._compiled:
            logger.info("Graph not compiled, compiling now...")
            self.compile()

        assert self._compiled is not None

        initial_state: AgentState = {
            "messages": [HumanMessage(content=str(input_data.get("message", "")))],
            "current_node": "",
            "input_data": input_data,
            "output_data": {},
        }
        logger.debug(f"Initial state: {initial_state}")

        config = RunnableConfig(configurable={"thread_id": thread_id})

        try:
            logger.info("Invoking compiled graph...")
            result = await self._compiled.ainvoke(initial_state, config)
            elapsed = time.time() - start_time
            logger.info(f"Graph execution completed in {elapsed:.2f}s")
            logger.debug(f"Result: {result}")
        except Exception as e:
            elapsed = time.time() - start_time
            logger.exception(f"Graph execution failed after {elapsed:.2f}s: {e}")
            raise

        output = {
            "messages": [
                {
                    "role": "ai" if isinstance(m, AIMessage) else "human",
                    "content": m.content,
                }
                for m in result.get("messages", [])
            ],
            "output_data": result.get("output_data", {}),
        }
        logger.info(f"Returning output with {len(output['messages'])} messages")
        return output
