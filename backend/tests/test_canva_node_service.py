from unittest.mock import AsyncMock, patch

import pytest

from app.services.canva_node_service import (
    create_canva_mcp_node,
    create_output_export_node,
)


@pytest.mark.asyncio
class TestCanvaMCPNode:
    """Test Canva MCP node factory."""

    @patch("app.services.canva_node_service.canva_service")
    async def test_create_design_operation(self, mock_service):
        """Test Canva node with create operation."""
        mock_service.create_design = AsyncMock(
            return_value=type(
                "Response",
                (),
                {
                    "success": True,
                    "design_id": "new-123",
                    "design_url": "https://canva.com/design/new-123",
                    "error": None,
                },
            )()
        )

        config = {
            "operation": "create",
            "designName": "Test Design",
            "outputFormat": "link",
        }

        node_fn = create_canva_mcp_node(config)

        state = {
            "design_intent": "Create a poster",
            "canva_instructions": {
                "design_type": "poster",
                "elements": [],
                "style_preferences": {},
            },
        }

        result = await node_fn(state)

        assert result["canva_success"] is True
        assert result["canva_design_id"] == "new-123"
        assert result["canva_design_url"] == "https://canva.com/design/new-123"
        assert result["canva_export_url"] is None

    @patch("app.services.canva_node_service.canva_service")
    async def test_create_with_export(self, mock_service):
        """Test Canva node with export."""
        mock_service.create_design = AsyncMock(
            return_value=type(
                "Response",
                (),
                {
                    "success": True,
                    "design_id": "new-456",
                    "design_url": "https://canva.com/design/new-456",
                    "error": None,
                },
            )()
        )
        mock_service.export_design = AsyncMock(
            return_value={
                "url": "https://canva.com/export/new-456.pdf",
            }
        )

        config = {
            "operation": "create",
            "outputFormat": "pdf",
        }

        node_fn = create_canva_mcp_node(config)

        state = {
            "canva_instructions": {
                "design_type": "document",
                "elements": [],
            },
        }

        result = await node_fn(state)

        assert result["canva_success"] is True
        assert result["canva_export_url"] == "https://canva.com/export/new-456.pdf"
        assert result["canva_export_format"] == "pdf"

    @patch("app.services.canva_node_service.canva_service")
    async def test_modify_design_operation(self, mock_service):
        """Test Canva node with modify operation."""
        mock_service.search_templates = AsyncMock(
            return_value=[{"id": "template-789", "title": "Modern Template"}]
        )
        mock_service.modify_design = AsyncMock(
            return_value=type(
                "Response",
                (),
                {
                    "success": True,
                    "design_id": "modified-789",
                    "design_url": "https://canva.com/design/modified-789",
                    "error": None,
                },
            )()
        )

        config = {
            "operation": "modify",
            "templateSource": "search",
            "templateSearchQuery": "modern template",
        }

        node_fn = create_canva_mcp_node(config)

        state = {
            "canva_instructions": {
                "design_type": "presentation",
                "elements": [{"type": "text", "content": "Updated"}],
            },
        }

        result = await node_fn(state)

        assert result["canva_success"] is True
        assert result["canva_design_id"] == "modified-789"

    @patch("app.services.canva_node_service.canva_service")
    async def test_error_handling(self, mock_service):
        """Test error handling in Canva node."""
        mock_service.create_design = AsyncMock(side_effect=Exception("API Error"))

        config = {"operation": "create"}
        node_fn = create_canva_mcp_node(config)

        state = {"canva_instructions": {}}
        result = await node_fn(state)

        assert result["canva_success"] is False
        assert "API Error" in result["canva_error"]


@pytest.mark.asyncio
class TestOutputExportNode:
    """Test output export node factory."""

    @patch("app.services.canva_node_service.export_service")
    async def test_export_node_with_link(self, mock_service):
        """Test output export node with link output."""
        mock_service.export_design = AsyncMock(
            return_value=type(
                "Result",
                (),
                {
                    "output_type": type("OutputType", (), {"value": "link"})(),
                    "url": "https://canva.com/design/test-123",
                    "filename": None,
                    "canva_edit_url": "https://canva.com/design/test-123",
                    "expires_at": None,
                },
            )()
        )

        config = {
            "outputType": "link",
            "downloadAutomatically": False,
            "showPreview": True,
        }

        node_fn = create_output_export_node(config)

        state = {
            "canva_design_id": "test-123",
            "canva_design_url": "https://canva.com/design/test-123",
        }

        result = await node_fn(state)

        assert "final_output" in result
        assert result["final_output"]["type"] == "link"
        assert result["final_output"]["url"] == "https://canva.com/design/test-123"

    @patch("app.services.canva_node_service.export_service")
    async def test_export_node_missing_design_url(self, mock_service):
        """Test output export node handles missing design URL."""
        config = {"outputType": "pdf"}
        node_fn = create_output_export_node(config)

        state = {}
        result = await node_fn(state)

        assert "error" in result["final_output"]

    @patch("app.services.canva_node_service.export_service")
    async def test_export_node_exception_handling(self, mock_service):
        """Test output export node error handling."""
        mock_service.export_design = AsyncMock(side_effect=Exception("Export failed"))

        config = {"outputType": "pdf"}
        node_fn = create_output_export_node(config)

        state = {
            "canva_design_id": "test-456",
            "canva_design_url": "https://canva.com/design/test-456",
        }

        result = await node_fn(state)

        assert "error" in result["final_output"]
        assert "Export failed" in result["final_output"]["error"]
