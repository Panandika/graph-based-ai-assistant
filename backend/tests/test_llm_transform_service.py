import json
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage

from app.services.llm_transform_service import (
    create_input_image_node,
    create_input_text_node,
    create_llm_transform_node,
    parse_llm_response,
)


class TestParseLLMResponse:
    """Test LLM response parsing functionality."""

    def test_parse_valid_json_response(self):
        """Test parsing a valid JSON response."""
        response = json.dumps(
            {
                "enhanced_text": "Professional presentation about AI",
                "design_intent": "Create a modern tech presentation",
                "canva_instructions": {
                    "action": "create",
                    "design_type": "presentation",
                    "elements": [],
                },
            }
        )

        result = parse_llm_response(response)

        assert result.enhanced_text == "Professional presentation about AI"
        assert result.design_intent == "Create a modern tech presentation"
        assert result.canva_instructions is not None
        assert result.canva_instructions["action"] == "create"

    def test_parse_json_in_code_block(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        response = """Here's the result:
```json
{
  "enhanced_text": "Test text",
  "design_intent": "Test intent",
  "canva_instructions": {"action": "create"}
}
```
"""
        result = parse_llm_response(response)

        assert result.enhanced_text == "Test text"
        assert result.design_intent == "Test intent"
        assert result.canva_instructions is not None

    def test_parse_plain_text_response(self):
        """Test parsing plain text when JSON extraction fails."""
        response = "This is just plain text without JSON structure"

        result = parse_llm_response(response)

        assert result.enhanced_text == response
        assert result.design_intent == ""
        assert result.canva_instructions is None
        assert result.raw_response == response

    def test_parse_malformed_json(self):
        """Test handling malformed JSON gracefully."""
        response = '{"enhanced_text": "incomplete'

        result = parse_llm_response(response)

        assert result.enhanced_text == response
        assert result.canva_instructions is None


@pytest.mark.asyncio
class TestInputNodes:
    """Test input node factories."""

    async def test_input_text_node(self):
        """Test input text node processes text correctly."""
        config = {}
        node_fn = await create_input_text_node(config)

        state = {
            "input_data": {
                "text": "Hello, world!",
            }
        }

        result = await node_fn(state)

        assert result["input_text"] == "Hello, world!"
        assert result["input_type"] == "text"

    async def test_input_text_node_empty(self):
        """Test input text node handles missing text."""
        config = {}
        node_fn = await create_input_text_node(config)

        state = {"input_data": {}}

        result = await node_fn(state)

        assert result["input_text"] == ""
        assert result["input_type"] == "text"

    async def test_input_image_node(self):
        """Test input image node processes image data correctly."""
        config = {}
        node_fn = await create_input_image_node(config)

        state = {
            "input_data": {
                "image": {
                    "url": "https://example.com/image.jpg",
                    "base64": "base64data",
                }
            }
        }

        result = await node_fn(state)

        assert result["input_image_url"] == "https://example.com/image.jpg"
        assert result["input_image_base64"] == "base64data"
        assert result["input_type"] == "image"

    async def test_input_text_node_fallback(self):
        """Test input text node falls back to config if input_data is missing text."""
        config = {"text": "Configured Text"}
        node_fn = await create_input_text_node(config)

        # Empty input data
        state = {"input_data": {}}

        result = await node_fn(state)

        assert result["input_text"] == "Configured Text"
        assert result["input_type"] == "text"

    async def test_input_text_node_priority(self):
        """Test input text node prioritizes input_data over config."""
        config = {"text": "Configured Text"}
        node_fn = await create_input_text_node(config)

        state = {
            "input_data": {
                "text": "Override Text",
            }
        }

        result = await node_fn(state)

        assert result["input_text"] == "Override Text"
        assert result["input_type"] == "text"

    async def test_input_image_node_fallback(self):
        """Test input image node falls back to config if input_data is missing image."""
        config = {"imageUrl": "https://config.com/image.jpg"}
        node_fn = await create_input_image_node(config)

        state = {"input_data": {}}

        result = await node_fn(state)

        assert result["input_image_url"] == "https://config.com/image.jpg"
        assert result["input_type"] == "image"

    async def test_input_image_node_priority(self):
        """Test input image node prioritizes input_data over config."""
        config = {"imageUrl": "https://config.com/image.jpg"}
        node_fn = await create_input_image_node(config)

        state = {
            "input_data": {
                "image": {
                    "url": "https://override.com/image.jpg",
                }
            }
        }

        result = await node_fn(state)

        assert result["input_image_url"] == "https://override.com/image.jpg"
        assert result["input_type"] == "image"


@pytest.mark.asyncio
class TestLLMTransformNode:
    """Test LLM transform node with vision support."""

    @patch("app.services.llm_transform_service.get_llm")
    async def test_text_only_transform(self, mock_get_llm):
        """Test LLM transform with text-only input."""
        mock_llm = AsyncMock()
        mock_response = AIMessage(
            content=json.dumps(
                {
                    "enhanced_text": "Enhanced content",
                    "design_intent": "Create a poster",
                    "canva_instructions": {
                        "action": "create",
                        "design_type": "poster",
                    },
                }
            )
        )
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_llm.return_value = mock_llm

        config = {
            "provider": "openai",
            "model": "gpt-4o",
            "systemPrompt": "Test prompt",
            "userPromptTemplate": "{{text}}",
            "enableVision": False,
            "temperature": 0.7,
            "maxTokens": 1000,
        }

        node_fn = create_llm_transform_node(config)

        state = {
            "input_text": "Create a poster about AI",
            "messages": [],
        }

        result = await node_fn(state)

        assert result["enhanced_text"] == "Enhanced content"
        assert result["design_intent"] == "Create a poster"
        assert result["canva_instructions"]["action"] == "create"
        assert len(result["messages"]) == 1

        mock_llm.ainvoke.assert_called_once()

    @patch("app.services.llm_transform_service.get_llm")
    async def test_vision_transform(self, mock_get_llm):
        """Test LLM transform with vision enabled and image input."""
        mock_llm = AsyncMock()
        mock_response = AIMessage(
            content=json.dumps(
                {
                    "enhanced_text": "Based on the image",
                    "design_intent": "Enhance the photo",
                    "canva_instructions": {
                        "action": "modify",
                        "design_type": "social_media",
                    },
                }
            )
        )
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_llm.return_value = mock_llm

        config = {
            "provider": "openai",
            "model": "gpt-4o",
            "enableVision": True,
            "imageDetail": "high",
        }

        node_fn = create_llm_transform_node(config)

        state = {
            "input_text": "Make this better",
            "input_image_url": "https://example.com/photo.jpg",
            "messages": [],
        }

        result = await node_fn(state)

        assert result["enhanced_text"] == "Based on the image"
        assert result["canva_instructions"]["design_type"] == "social_media"

        call_args = mock_llm.ainvoke.call_args[0][0]
        assert len(call_args) > 0
        last_message = call_args[-1]
        assert isinstance(last_message.content, list)
        has_image = any(
            part.get("type") == "image_url" for part in last_message.content
        )
        assert has_image

    @patch("app.services.llm_transform_service.get_llm")
    async def test_transform_with_invalid_provider(self, mock_get_llm):
        """Test LLM transform falls back to default provider on invalid config."""
        mock_llm = AsyncMock()
        mock_response = AIMessage(content="Response")
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_llm.return_value = mock_llm

        config = {
            "provider": "invalid_provider",
            "model": "gpt-4o",
        }

        node_fn = create_llm_transform_node(config)

        state = {
            "input_text": "Test",
            "messages": [],
        }

        result = await node_fn(state)

        assert "enhanced_text" in result
        mock_get_llm.assert_called_once()

    @patch("app.services.llm_transform_service.get_llm")
    async def test_transform_preserves_state_messages(self, mock_get_llm):
        """Test that transform node preserves existing messages in state."""
        mock_llm = AsyncMock()
        mock_response = AIMessage(content="New response")
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_llm.return_value = mock_llm

        config = {"provider": "openai", "model": "gpt-4o"}
        node_fn = create_llm_transform_node(config)

        existing_message = AIMessage(content="Previous message")
        state = {
            "input_text": "Test",
            "messages": [existing_message],
        }

        result = await node_fn(state)

        assert len(result["messages"]) == 2
        assert result["messages"][0] == existing_message
