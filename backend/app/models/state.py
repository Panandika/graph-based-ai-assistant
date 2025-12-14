from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """State container for agent workflow execution."""

    messages: Annotated[list[BaseMessage], add_messages]
    current_node: str
    input_data: dict[str, Any]
    output_data: dict[str, Any]

    # Input Node State
    input_text: str
    input_type: str
    input_image_url: str
    input_image_base64: str | None

    # LLM Transform State
    enhanced_text: str
    design_intent: str
    canva_instructions: dict[str, Any]
    llm_raw_response: str

    # Canva Node State
    canva_design_id: str
    canva_design_url: str
    canva_export_url: str | None
    canva_export_format: str
    canva_success: bool
    canva_error: str

    # Output State
    final_output: dict[str, Any]
