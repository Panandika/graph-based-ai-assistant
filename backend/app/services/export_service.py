import logging
from datetime import UTC, datetime, timedelta

from app.schemas.export import OutputExportNodeConfig, OutputExportResult, OutputType

logger = logging.getLogger(__name__)


class ExportService:
    """Service for handling design export operations."""

    async def export_design(
        self,
        design_id: str,
        design_url: str,
        config: OutputExportNodeConfig,
        export_url: str | None = None,
    ) -> OutputExportResult:
        """
        Export a Canva design based on configuration.

        Args:
            design_id: The Canva design ID
            design_url: The editable Canva design URL
            config: Export configuration
            export_url: Optional pre-exported URL from Canva MCP node

        Returns:
            OutputExportResult with the exported file/link details
        """
        output_type = config.output_type
        url = export_url or design_url

        if output_type == OutputType.LINK:
            return await self._handle_link_export(design_id, design_url, config)
        elif output_type in (OutputType.PDF, OutputType.IMAGE):
            return await self._handle_file_export(design_id, design_url, url, config)
        else:
            raise ValueError(f"Unsupported output type: {output_type}")

    async def _handle_link_export(
        self,
        design_id: str,
        design_url: str,
        config: OutputExportNodeConfig,
    ) -> OutputExportResult:
        """Handle link-based export."""
        link_options = config.link_options

        # access_level = "edit"
        expires_at = None

        if link_options and link_options.expires_in:
            expires_at = (
                datetime.now(UTC) + timedelta(hours=link_options.expires_in)
            ).isoformat()

        return OutputExportResult(
            output_type=OutputType.LINK,
            url=design_url,
            canva_edit_url=design_url,
            expires_at=expires_at,
        )

    async def _handle_file_export(
        self,
        design_id: str,
        design_url: str,
        export_url: str,
        config: OutputExportNodeConfig,
    ) -> OutputExportResult:
        """Handle PDF/image file export."""
        if config.output_type == OutputType.PDF:
            format_ext = "pdf"
            filename = f"design_{design_id}.pdf"
        else:
            image_options = config.image_options
            if image_options:
                format_ext = image_options.format.value
                filename = f"design_{design_id}.{format_ext}"
            else:
                format_ext = "png"
                filename = f"design_{design_id}.png"

        return OutputExportResult(
            output_type=config.output_type,
            url=export_url,
            filename=filename,
            canva_edit_url=design_url,
        )


export_service = ExportService()
