import logging
from typing import Any

from langchain_core.tools import BaseTool

from app.core.mcp import mcp_manager
from app.schemas.canva import CanvaDesignResponse

logger = logging.getLogger(__name__)


class CanvaService:
    """
    High-level service for Canva operations.
    Wraps MCP tools with business logic.
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    async def _ensure_tools(self) -> None:
        """Ensure Canva tools are loaded."""
        if not self._tools:
            tools = await mcp_manager.get_canva_tools()
            self._tools = {t.name: t for t in tools}
            logger.info(f"Loaded {len(self._tools)} Canva tools")

    async def create_design(
        self,
        design_type: str,
        title: str,
        elements: list[dict[str, Any]],
        style: dict[str, Any] | None = None,
    ) -> CanvaDesignResponse:
        """Create a new Canva design."""
        await self._ensure_tools()

        create_tool = self._tools.get("canva_create_design")
        if not create_tool:
            logger.warning(
                "Canva create_design tool not available, using mock response"
            )
            return CanvaDesignResponse(
                success=True,
                design_id="mock-design-id",
                design_url="https://canva.com/design/mock-design-id",
                error="Tool not available - mock response",
            )

        try:
            result = await create_tool.ainvoke(
                {
                    "design_type": design_type,
                    "title": title,
                    "elements": elements,
                    "style": style,
                }
            )

            return CanvaDesignResponse.model_validate(result)
        except Exception as e:
            logger.error(f"Failed to create Canva design: {e}")
            return CanvaDesignResponse(
                success=False,
                design_id="",
                design_url="",
                error=str(e),
            )

    async def search_templates(
        self,
        query: str,
        design_type: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for Canva templates."""
        await self._ensure_tools()

        search_tool = self._tools.get("canva_search_templates")
        if not search_tool:
            logger.warning("Canva search_templates tool not available")
            return []

        try:
            result = await search_tool.ainvoke(
                {
                    "query": query,
                    "design_type": design_type,
                    "limit": limit,
                }
            )

            return result.get("templates", [])  # type: ignore
        except Exception as e:
            logger.error(f"Failed to search Canva templates: {e}")
            return []

    async def modify_design(
        self,
        design_id: str,
        modifications: list[dict[str, Any]],
    ) -> CanvaDesignResponse:
        """Modify an existing design."""
        await self._ensure_tools()

        modify_tool = self._tools.get("canva_modify_design")
        if not modify_tool:
            logger.warning(
                "Canva modify_design tool not available, using mock response"
            )
            return CanvaDesignResponse(
                success=True,
                design_id=design_id,
                design_url=f"https://canva.com/design/{design_id}",
                error="Tool not available - mock response",
            )

        try:
            result = await modify_tool.ainvoke(
                {
                    "design_id": design_id,
                    "modifications": modifications,
                }
            )

            return CanvaDesignResponse.model_validate(result)
        except Exception as e:
            logger.error(f"Failed to modify Canva design: {e}")
            return CanvaDesignResponse(
                success=False,
                design_id=design_id,
                design_url="",
                error=str(e),
            )

    async def export_design(
        self,
        design_id: str,
        format: str,
        quality: str = "standard",
    ) -> dict[str, Any]:
        """Export design to specified format."""
        await self._ensure_tools()

        export_tool = self._tools.get("canva_export_design")
        if not export_tool:
            logger.warning("Canva export_design tool not available")
            return {
                "url": f"https://canva.com/export/{design_id}.{format}",
                "format": format,
                "error": "Tool not available - mock response",
            }

        try:
            return await export_tool.ainvoke(  # type: ignore
                {
                    "design_id": design_id,
                    "format": format,
                    "quality": quality,
                }
            )
        except Exception as e:
            logger.error(f"Failed to export Canva design: {e}")
            return {
                "url": "",
                "format": format,
                "error": str(e),
            }


canva_service: CanvaService = CanvaService()
