import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel, ValidationError

from app.core.config import LLMProvider, get_settings
from app.core.llm import get_llm
from app.schemas.canva import CanvaInstructions

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
) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]:
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

    async def llm_transform_node(state: dict[str, Any]) -> dict[str, Any]:
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
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": image_url,
                    "detail": image_detail,
                },
            })

        if content_parts:
            if len(content_parts) == 1 and content_parts[0]["type"] == "text":
                messages.append(HumanMessage(content=content_parts[0]["text"]))
            else:
                messages.append(HumanMessage(content=content_parts))

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


async def create_input_text_node(
    node_config: dict[str, Any],
) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]:
    """Factory for input text node."""

    async def input_text_node(state: dict[str, Any]) -> dict[str, Any]:
        user_input = state.get("user_input", {})
        text = user_input.get("text", "")

        return {
            "input_text": text,
            "input_type": "text",
        }

    return input_text_node


async def create_input_image_node(
    node_config: dict[str, Any],
) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]:
    """Factory for input image node."""

    async def input_image_node(state: dict[str, Any]) -> dict[str, Any]:
        user_input = state.get("user_input", {})
        image_data = user_input.get("image", {})

        return {
            "input_image_url": image_data.get("url"),
            "input_image_base64": image_data.get("base64"),
            "input_type": "image",
        }

    return input_image_node
