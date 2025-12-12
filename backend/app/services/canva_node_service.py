import logging
from collections.abc import Awaitable, Callable
from typing import Any

from app.schemas.export import OutputExportNodeConfig
from app.services.canva_service import canva_service
from app.services.export_service import export_service

logger = logging.getLogger(__name__)


def create_canva_mcp_node(
    node_config: dict[str, Any],
) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]:
    """Factory for Canva MCP node using langchain-mcp-adapters."""

    operation = node_config.get("operation", "create")
    output_format = node_config.get("outputFormat", "link")
    template_source = node_config.get("templateSource", "from_input")
    template_id = node_config.get("templateId")
    template_search_query = node_config.get("templateSearchQuery")
    design_name = node_config.get("designName", "Untitled Design")

    async def canva_mcp_node(state: dict[str, Any]) -> dict[str, Any]:
        """Execute Canva MCP operations."""
        instructions = state.get("canva_instructions", {})

        try:
            if operation == "create":
                result = await canva_service.create_design(
                    design_type=instructions.get("design_type", "document"),
                    title=design_name or state.get("design_intent", "Untitled"),
                    elements=instructions.get("elements", []),
                    style=instructions.get("style_preferences"),
                )
            else:
                resolved_template_id = await _resolve_template(
                    template_source,
                    template_id,
                    template_search_query,
                    instructions,
                )
                result = await canva_service.modify_design(
                    design_id=resolved_template_id,
                    modifications=instructions.get("elements", []),
                )

            export_url = None
            if output_format != "link" and result.success:
                export_result = await canva_service.export_design(
                    design_id=result.design_id,
                    format=output_format,
                )
                export_url = export_result.get("url")

            return {
                "canva_design_id": result.design_id,
                "canva_design_url": result.design_url,
                "canva_export_url": export_url,
                "canva_export_format": output_format,
                "canva_success": result.success,
                "canva_error": result.error,
            }

        except Exception as e:
            logger.error(f"Canva MCP node error: {e}")
            return {
                "canva_design_id": "",
                "canva_design_url": "",
                "canva_export_url": None,
                "canva_success": False,
                "canva_error": str(e),
            }

    return canva_mcp_node


async def _resolve_template(
    template_source: str,
    template_id: str | None,
    template_search_query: str | None,
    instructions: dict[str, Any],
) -> str:
    """Resolve template ID from various sources."""
    if template_source == "id" and template_id:
        return template_id

    query = template_search_query or instructions.get("template_query", "")
    if not query:
        raise ValueError("No template query provided")

    templates = await canva_service.search_templates(
        query=query,
        design_type=instructions.get("design_type"),
        limit=1,
    )

    if templates:
        return str(templates[0]["id"])

    raise ValueError(f"No template found for query: {query}")


def create_output_export_node(
    node_config: dict[str, Any],
) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]:
    """Factory for output export node."""

    try:
        config = OutputExportNodeConfig.model_validate(node_config)
    except Exception as e:
        logger.warning(f"Invalid export config: {e}, using defaults")
        config = OutputExportNodeConfig(
            output_type="link",  # type: ignore
            download_automatically=False,
            show_preview=True,
        )

    async def output_export_node(state: dict[str, Any]) -> dict[str, Any]:
        """Process output export."""
        design_id = state.get("canva_design_id", "")
        design_url = state.get("canva_design_url", "")
        export_url = state.get("canva_export_url")

        if not design_url:
            logger.warning("No design URL available for export")
            return {
                "final_output": {
                    "type": config.output_type.value,
                    "url": "",
                    "error": "No design URL available",
                }
            }

        try:
            result = await export_service.export_design(
                design_id=design_id,
                design_url=design_url,
                config=config,
                export_url=export_url,
            )

            return {
                "final_output": {
                    "type": result.output_type.value,
                    "url": result.url,
                    "filename": result.filename,
                    "edit_url": result.canva_edit_url,
                    "expires_at": result.expires_at,
                }
            }

        except Exception as e:
            logger.error(f"Export node error: {e}")
            return {
                "final_output": {
                    "type": config.output_type.value,
                    "url": design_url,
                    "error": str(e),
                }
            }

    return output_export_node
