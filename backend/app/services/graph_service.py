from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from app.core.config import get_settings
from app.core.llm import get_llm
from app.db.database import get_client
from app.models.graph import Graph, NodeType


class AgentState(TypedDict):
    """State container for agent workflow execution."""

    messages: Annotated[list[BaseMessage], add_messages]
    current_node: str
    input_data: dict[str, Any]
    output_data: dict[str, Any]


async def get_checkpointer() -> AsyncMongoDBSaver:
    """Get MongoDB checkpointer for state persistence."""
    settings = get_settings()
    client = get_client()
    return AsyncMongoDBSaver(client, db_name=settings.database_name)


async def llm_node(state: AgentState) -> dict[str, Any]:
    """Process state through LLM."""
    llm = get_llm()
    response = await llm.ainvoke(state["messages"])
    return {
        "messages": [response],
        "output_data": {"response": response.content},
    }


async def tool_node(state: AgentState) -> dict[str, Any]:
    """Execute a tool based on state."""
    return {
        "output_data": {"tool_result": "Tool executed successfully"},
    }


def create_condition_router(condition_config: dict[str, Any]):
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
        self._compiled = None

    def _build_graph(self) -> StateGraph:
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
                builder.add_node(node_id, llm_node)
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
                    path_map = {}
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
                            path_map,
                        )
            else:
                if source == START:
                    builder.add_edge(START, target)
                elif target == END:
                    builder.add_edge(source, END)
                elif source not in [START, END] and target not in [START, END]:
                    builder.add_edge(source, target)

        return builder

    async def compile(self) -> None:
        """Compile the graph for execution."""
        builder = self._build_graph()
        checkpointer = await get_checkpointer()
        self._compiled = builder.compile(checkpointer=checkpointer)

    async def execute(
        self,
        thread_id: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the workflow with the given input."""
        if not self._compiled:
            await self.compile()

        initial_state: AgentState = {
            "messages": [HumanMessage(content=str(input_data.get("message", "")))],
            "current_node": "",
            "input_data": input_data,
            "output_data": {},
        }

        config = {"configurable": {"thread_id": thread_id}}

        result = await self._compiled.ainvoke(initial_state, config)

        return {
            "messages": [
                {"role": "ai" if isinstance(m, AIMessage) else "human", "content": m.content}
                for m in result.get("messages", [])
            ],
            "output_data": result.get("output_data", {}),
        }
