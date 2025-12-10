from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.canva_service import CanvaService


@pytest.fixture
def mock_mcp_manager():
    """Mock the MCP manager for testing."""
    with patch("app.services.canva_service.mcp_manager") as mock:
        mock_create_tool = MagicMock()
        mock_create_tool.name = "canva_create_design"
        mock_create_tool.ainvoke = AsyncMock(return_value={
            "success": True,
            "design_id": "test-123",
            "design_url": "https://canva.com/design/test-123",
        })

        mock_search_tool = MagicMock()
        mock_search_tool.name = "canva_search_templates"
        mock_search_tool.ainvoke = AsyncMock(return_value={
            "templates": [
                {
                    "id": "template-1",
                    "title": "Modern Presentation",
                    "thumbnail_url": "https://example.com/thumb1.jpg",
                    "design_type": "presentation",
                }
            ]
        })

        mock_modify_tool = MagicMock()
        mock_modify_tool.name = "canva_modify_design"
        mock_modify_tool.ainvoke = AsyncMock(return_value={
            "success": True,
            "design_id": "modified-123",
            "design_url": "https://canva.com/design/modified-123",
        })

        mock_export_tool = MagicMock()
        mock_export_tool.name = "canva_export_design"
        mock_export_tool.ainvoke = AsyncMock(return_value={
            "url": "https://canva.com/export/test-123.pdf",
            "format": "pdf",
        })

        mock.get_canva_tools = AsyncMock(return_value=[
            mock_create_tool,
            mock_search_tool,
            mock_modify_tool,
            mock_export_tool,
        ])

        yield mock


@pytest.mark.asyncio
class TestCanvaService:
    """Test Canva service functionality."""

    async def test_create_design(self, mock_mcp_manager):
        """Test design creation via MCP tools."""
        service = CanvaService()

        result = await service.create_design(
            design_type="presentation",
            title="Test Design",
            elements=[],
        )

        assert result.success is True
        assert result.design_id == "test-123"
        assert "canva.com" in result.design_url

    async def test_search_templates(self, mock_mcp_manager):
        """Test template search via MCP tools."""
        service = CanvaService()

        result = await service.search_templates(
            query="modern presentation",
            design_type="presentation",
            limit=5,
        )

        assert len(result) == 1
        assert result[0]["id"] == "template-1"
        assert result[0]["title"] == "Modern Presentation"

    async def test_modify_design(self, mock_mcp_manager):
        """Test design modification via MCP tools."""
        service = CanvaService()

        result = await service.modify_design(
            design_id="existing-123",
            modifications=[{"type": "text", "content": "Updated"}],
        )

        assert result.success is True
        assert result.design_id == "modified-123"

    async def test_export_design(self, mock_mcp_manager):
        """Test design export via MCP tools."""
        service = CanvaService()

        result = await service.export_design(
            design_id="test-123",
            format="pdf",
            quality="standard",
        )

        assert "url" in result
        assert result["format"] == "pdf"
        assert "pdf" in result["url"]

    async def test_create_design_tool_not_available(self):
        """Test error handling when tool is not available."""
        with patch("app.services.canva_service.mcp_manager") as mock:
            mock.get_canva_tools = AsyncMock(return_value=[])

            service = CanvaService()

            result = await service.create_design(
                design_type="presentation",
                title="Test",
                elements=[],
            )

            assert result.success is True
            assert "mock" in result.design_id.lower()
            assert result.error is not None

    async def test_create_design_exception_handling(self, mock_mcp_manager):
        """Test exception handling during design creation."""
        mock_tool = MagicMock()
        mock_tool.name = "canva_create_design"
        mock_tool.ainvoke = AsyncMock(side_effect=Exception("API Error"))

        with patch("app.services.canva_service.mcp_manager") as mock:
            mock.get_canva_tools = AsyncMock(return_value=[mock_tool])

            service = CanvaService()

            result = await service.create_design(
                design_type="presentation",
                title="Test",
                elements=[],
            )

            assert result.success is False
            assert "API Error" in result.error

    async def test_search_templates_no_results(self, mock_mcp_manager):
        """Test template search with no results."""
        mock_tool = MagicMock()
        mock_tool.name = "canva_search_templates"
        mock_tool.ainvoke = AsyncMock(return_value={"templates": []})

        with patch("app.services.canva_service.mcp_manager") as mock:
            mock.get_canva_tools = AsyncMock(return_value=[mock_tool])

            service = CanvaService()

            result = await service.search_templates(query="nonexistent")

            assert len(result) == 0
