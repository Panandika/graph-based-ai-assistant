import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel

from app.core.config import LLMProvider
from app.core.llm import get_llm
from app.models.state import AgentState

logger = logging.getLogger(__name__)

DEFAULT_TRANSFORM_PROMPT = """You are a design assistant that transforms user input into actionable design instructions for Canva.

Given the user's input (text and/or image), you will:
1. Understand the user's design intent
2. Transform and enhance any text content for the design
3. Generate specific instructions for creating/modifying a Canva design

Output your response in the following JSON structure:
{
  "enhanced_text": "The transformed/enhanced text content",
  "design_intent": "Brief description of what the user wants",
  "canva_instructions": {
    "action": "create" or "modify",
    "design_type": "presentation" | "social_media" | "document" | "poster" | etc,
    "template_query": "search query for template if modifying",
    "elements": [
      {
        "type": "text" | "image" | "shape",
        "content": "...",
        "style": {...}
      }
    ],
    "style_preferences": {
      "color_scheme": "...",
      "font_style": "...",
      "mood": "..."
    }
  }
}"""


class LLMTransformOutput(BaseModel):
    """Structured output from LLM transform node."""

    enhanced_text: str = ""
    design_intent: str = ""
    canva_instructions: dict[str, Any] | None = None
    raw_response: str = ""


def parse_llm_response(response_content: str) -> LLMTransformOutput:
    """Parse LLM response, attempting to extract JSON if present."""
    raw = response_content.strip()

    try:
        json_match = raw
        if "```json" in raw:
            start = raw.find("```json") + 7
            end = raw.find("```", start)
            json_match = raw[start:end].strip()
        elif "```" in raw:
            start = raw.find("```") + 3
            end = raw.find("```", start)
            json_match = raw[start:end].strip()

        if json_match.startswith("{"):
            parsed = json.loads(json_match)
            return LLMTransformOutput(
                enhanced_text=parsed.get("enhanced_text", ""),
                design_intent=parsed.get("design_intent", ""),
                canva_instructions=parsed.get("canva_instructions"),
                raw_response=raw,
            )
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse JSON from LLM response: {e}")

    return LLMTransformOutput(
        enhanced_text=raw,
        design_intent="",
        canva_instructions=None,
        raw_response=raw,
    )


def create_llm_transform_node(
    node_config: dict[str, Any],
) -> Callable[[AgentState], Awaitable[dict[str, Any]]]:
    """Factory to create an LLM transform node with vision support."""
    provider_str = node_config.get("provider", "openai")
    model = node_config.get("model", "gpt-4o")
    system_prompt = node_config.get("systemPrompt", DEFAULT_TRANSFORM_PROMPT)
    user_template = node_config.get("userPromptTemplate", "{{text}}")
    enable_vision = node_config.get("enableVision", True)
    image_detail = node_config.get("imageDetail", "auto")
    temperature = node_config.get("temperature", 0.7)
    max_tokens = node_config.get("maxTokens", 2000)

    try:
        provider = LLMProvider(provider_str)
    except ValueError:
        provider = LLMProvider.OPENAI

    async def llm_transform_node(state: AgentState) -> dict[str, Any]:
        """Process input through LLM with vision support."""
        llm = get_llm(
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        messages: list[BaseMessage] = []

        if system_prompt:
            messages.append(HumanMessage(content=system_prompt))

        content_parts: list[dict[str, Any]] = []

        input_text = state.get("input_text", "")
        if input_text:
            text_content = user_template.replace("{{text}}", input_text)
            content_parts.append({"type": "text", "text": text_content})

        if enable_vision and state.get("input_image_url"):
            image_url = state["input_image_url"]
            content_parts.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url,
                        "detail": image_detail,
                    },
                }
            )

        if content_parts:
            if len(content_parts) == 1 and content_parts[0]["type"] == "text":
                messages.append(HumanMessage(content=content_parts[0]["text"]))
            else:
                messages.append(HumanMessage(content=content_parts))  # type: ignore

        response = await llm.ainvoke(messages)
        parsed = parse_llm_response(str(response.content))

        return {
            "enhanced_text": parsed.enhanced_text,
            "design_intent": parsed.design_intent,
            "canva_instructions": parsed.canva_instructions or {},
            "llm_raw_response": parsed.raw_response,
            "messages": state.get("messages", []) + [response],
        }

    return llm_transform_node


def create_input_text_node(
    node_config: dict[str, Any],
) -> Callable[[AgentState], Awaitable[dict[str, Any]]]:
    """Factory for input text node."""

    async def input_text_node(state: AgentState) -> dict[str, Any]:
        logger.info("Executing INPUT_TEXT node...")
        logger.debug(f"  node_config: {node_config}")
        input_data = state.get("input_data", {})

        # The frontend stores the text in multiple possible locations:
        # 1. input_data.text (from execution parameters)
        # 2. node_config.value.text (from the InputTextNodeConfig component)
        # 3. node_config.text (legacy/direct config)
        value_obj = node_config.get("value", {})
        text = (
            input_data.get("text")
            or value_obj.get("text", "")
            or node_config.get("text", "")
        )

        logger.info(
            f"  Input text: '{text[:100]}...' (len={len(text)})"
            if len(text) > 100
            else f"  Input text: '{text}'"
        )

        result = {
            "input_text": text,
            "input_type": "text",
        }
        logger.info(f"  OUTPUT: input_type='text', input_text length={len(text)}")
        return result

    return input_text_node


def create_input_image_node(
    node_config: dict[str, Any],
) -> Callable[[AgentState], Awaitable[dict[str, Any]]]:
    """Factory for input image node."""

    async def input_image_node(state: AgentState) -> dict[str, Any]:
        logger.info("Executing INPUT_IMAGE node...")
        input_data = state.get("input_data", {})
        image_data = input_data.get("image", {})

        # Fallback values from node config
        config_url = node_config.get("imageUrl", "")

        # Priority: input_data > node_config
        url = image_data.get("url") or config_url
        base64_data = image_data.get("base64")

        logger.info(f"  Image URL: {url[:80] if url else 'None'}...")
        logger.info(f"  Base64 data present: {bool(base64_data)}")

        result = {
            "input_image_url": url,
            "input_image_base64": base64_data,
            "input_type": "image",
        }
        logger.info(
            f"  OUTPUT: input_type='image', url={bool(url)}, base64={bool(base64_data)}"
        )
        return result

    return input_image_node


# Keys that each node type produces - used by OUTPUT node to know what to collect
NODE_OUTPUT_KEYS = {
    "input_text": ["input_text", "input_type"],
    "input_image": ["input_image_url", "input_image_base64", "input_type"],
    "llm_transform": [
        "enhanced_text",
        "design_intent",
        "canva_instructions",
        "llm_raw_response",
    ],
    "canva_mcp": [
        "canva_design_id",
        "canva_design_url",
        "canva_export_url",
        "canva_success",
        "canva_error",
    ],
    "output_export": ["final_output"],
    "llm": ["output_data"],
}

# All possible state keys that could contain useful data
ALL_STATE_KEYS = [
    "input_text",
    "input_type",
    "input_image_url",
    "input_image_base64",
    "enhanced_text",
    "design_intent",
    "canva_instructions",
    "llm_raw_response",
    "canva_design_id",
    "canva_design_url",
    "canva_export_url",
    "canva_success",
    "canva_error",
    "final_output",
]


def create_output_node(
    node_config: dict[str, Any],
) -> Callable[[AgentState], Awaitable[dict[str, Any]]]:
    """Factory for output collection node.

    This node collects available state values and puts them into output_data.
    By default, it collects all non-empty values from known state keys.
    """
    # User can optionally specify which keys to collect
    include_keys = node_config.get("include_keys")  # None means all

    async def output_node(state: AgentState) -> dict[str, Any]:
        logger.info("Executing OUTPUT (collect) node...")

        collected: dict[str, Any] = {}

        # Determine which keys to collect
        keys_to_check = include_keys if include_keys else ALL_STATE_KEYS

        for key in keys_to_check:
            value = state.get(key)
            # Only include non-None, non-empty values
            if value is not None and value != "" and value != {}:
                collected[key] = value
                logger.info(f"  Collected: {key} = {str(value)[:100]}...")

        if not collected:
            logger.warning("  No data to collect from state")
        else:
            logger.info(f"  Total collected: {len(collected)} keys")

        return {
            "output_data": collected,
        }

    return output_node
