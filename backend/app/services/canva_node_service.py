import logging
from collections.abc import Awaitable, Callable
from typing import Any

from app.models.state import AgentState
from app.schemas.export import OutputExportNodeConfig
from app.services.canva_service import canva_service
from app.services.export_service import export_service

logger = logging.getLogger(__name__)


def create_canva_mcp_node(
    node_config: dict[str, Any],
) -> Callable[[AgentState], Awaitable[dict[str, Any]]]:
    """Factory for Canva MCP node using langchain-mcp-adapters."""

    operation = node_config.get("operation", "create")
    output_format = node_config.get("outputFormat", "link")
    template_source = node_config.get("templateSource", "from_input")
    template_id = node_config.get("templateId")
    template_search_query = node_config.get("templateSearchQuery")
    design_name = node_config.get("designName", "Untitled Design")

    async def canva_mcp_node(state: AgentState) -> dict[str, Any]:
        """Execute Canva MCP operations."""
        logger.info(f"Executing CANVA_MCP node... operation={operation}")
        instructions = state.get("canva_instructions", {})
        logger.info(f"  Instructions: {instructions}")

        try:
            if operation == "create":
                logger.info(
                    f"  Creating design: type={instructions.get('design_type', 'document')}, name={design_name}"
                )
                result = await canva_service.create_design(
                    design_type=instructions.get("design_type", "document"),
                    title=design_name or state.get("design_intent", "Untitled"),
                    elements=instructions.get("elements", []),
                    style=instructions.get("style_preferences"),
                )
            else:
                logger.info(f"  Modifying design: template_source={template_source}")
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

            logger.info(
                f"  Design result: success={result.success}, design_id={result.design_id}"
            )

            export_url = None
            if output_format != "link" and result.success:
                logger.info(f"  Exporting design: format={output_format}")
                export_result = await canva_service.export_design(
                    design_id=result.design_id,
                    format=output_format,
                )
                export_url = export_result.get("url")
                logger.info(f"  Export URL: {export_url}")

            output = {
                "canva_design_id": result.design_id,
                "canva_design_url": result.design_url,
                "canva_export_url": export_url,
                "canva_export_format": output_format,
                "canva_success": result.success,
                "canva_error": result.error,
            }
            logger.info(
                f"  OUTPUT: success={result.success}, design_url={result.design_url[:50] if result.design_url else 'None'}..."
            )
            return output

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
) -> Callable[[AgentState], Awaitable[dict[str, Any]]]:
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

    async def output_export_node(state: AgentState) -> dict[str, Any]:
        """Process output export."""
        logger.info("Executing OUTPUT_EXPORT node...")
        design_id = state.get("canva_design_id", "")
        design_url = state.get("canva_design_url", "")
        export_url = state.get("canva_export_url")
        logger.info(
            f"  Design ID: {design_id}, URL: {design_url[:50] if design_url else 'None'}..."
        )

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
            logger.info(
                f"  Exporting with config: output_type={config.output_type.value}"
            )
            result = await export_service.export_design(
                design_id=design_id,
                design_url=design_url,
                config=config,
                export_url=export_url,
            )

            output = {
                "final_output": {
                    "type": result.output_type.value,
                    "url": result.url,
                    "filename": result.filename,
                    "edit_url": result.canva_edit_url,
                    "expires_at": result.expires_at,
                }
            }
            logger.info(
                f"  OUTPUT: type={result.output_type.value}, url={result.url[:50] if result.url else 'None'}..."
            )
            return output

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
