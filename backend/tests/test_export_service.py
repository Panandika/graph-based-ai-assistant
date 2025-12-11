import pytest

from app.schemas.export import (
    AccessLevel,
    ImageFormat,
    ImageOptions,
    LinkOptions,
    OutputExportNodeConfig,
    OutputType,
    PDFOptions,
    PDFQuality,
    PageSize,
)
from app.services.export_service import ExportService


@pytest.fixture
def export_service():
    """Create export service instance for testing."""
    return ExportService()


@pytest.mark.asyncio
class TestExportService:
    """Test export service functionality."""

    async def test_export_link_with_edit_access(self, export_service):
        """Test link export with edit access."""
        config = OutputExportNodeConfig(
            output_type=OutputType.LINK,
            link_options=LinkOptions(
                access_level=AccessLevel.EDIT,
                expires_in=24,
            ),
            download_automatically=False,
            show_preview=True,
        )

        result = await export_service.export_design(
            design_id="test-123",
            design_url="https://canva.com/design/test-123",
            config=config,
        )

        assert result.output_type == OutputType.LINK
        assert result.url == "https://canva.com/design/test-123"
        assert result.canva_edit_url == "https://canva.com/design/test-123"
        assert result.expires_at is not None

    async def test_export_link_with_view_access(self, export_service):
        """Test link export with view-only access."""
        config = OutputExportNodeConfig(
            output_type=OutputType.LINK,
            link_options=LinkOptions(
                access_level=AccessLevel.VIEW,
                expires_in=None,
            ),
            download_automatically=False,
            show_preview=True,
        )

        result = await export_service.export_design(
            design_id="test-456",
            design_url="https://canva.com/design/test-456",
            config=config,
        )

        assert result.output_type == OutputType.LINK
        assert result.url == "https://canva.com/design/test-456"
        assert result.expires_at is None

    async def test_export_pdf_with_options(self, export_service):
        """Test PDF export with custom options."""
        config = OutputExportNodeConfig(
            output_type=OutputType.PDF,
            pdf_options=PDFOptions(
                page_size=PageSize.A4,
                quality=PDFQuality.PRINT,
            ),
            download_automatically=True,
            show_preview=False,
        )

        result = await export_service.export_design(
            design_id="test-789",
            design_url="https://canva.com/design/test-789",
            config=config,
            export_url="https://canva.com/export/test-789.pdf",
        )

        assert result.output_type == OutputType.PDF
        assert result.url == "https://canva.com/export/test-789.pdf"
        assert result.filename == "design_test-789.pdf"
        assert result.canva_edit_url == "https://canva.com/design/test-789"

    async def test_export_image_png(self, export_service):
        """Test PNG image export."""
        config = OutputExportNodeConfig(
            output_type=OutputType.IMAGE,
            image_options=ImageOptions(
                format=ImageFormat.PNG,
                quality=95,
                scale=2.0,
            ),
            download_automatically=False,
            show_preview=True,
        )

        result = await export_service.export_design(
            design_id="test-png",
            design_url="https://canva.com/design/test-png",
            config=config,
            export_url="https://canva.com/export/test-png.png",
        )

        assert result.output_type == OutputType.IMAGE
        assert result.url == "https://canva.com/export/test-png.png"
        assert result.filename == "design_test-png.png"

    async def test_export_image_jpg(self, export_service):
        """Test JPG image export."""
        config = OutputExportNodeConfig(
            output_type=OutputType.IMAGE,
            image_options=ImageOptions(
                format=ImageFormat.JPG,
                quality=85,
                scale=1.0,
            ),
            download_automatically=True,
            show_preview=False,
        )

        result = await export_service.export_design(
            design_id="test-jpg",
            design_url="https://canva.com/design/test-jpg",
            config=config,
            export_url="https://canva.com/export/test-jpg.jpg",
        )

        assert result.output_type == OutputType.IMAGE
        assert result.filename == "design_test-jpg.jpg"

    async def test_export_image_default_png(self, export_service):
        """Test image export defaults to PNG when options missing."""
        config = OutputExportNodeConfig(
            output_type=OutputType.IMAGE,
            download_automatically=False,
            show_preview=True,
        )

        result = await export_service.export_design(
            design_id="test-default",
            design_url="https://canva.com/design/test-default",
            config=config,
            export_url="https://canva.com/export/test-default.png",
        )

        assert result.filename == "design_test-default.png"

    async def test_export_unsupported_type(self, export_service):
        """Test handling of invalid output type."""
        config = OutputExportNodeConfig(
            output_type="invalid",  # type: ignore
            download_automatically=False,
            show_preview=True,
        )

        with pytest.raises(ValueError, match="Unsupported output type"):
            await export_service.export_design(
                design_id="test-invalid",
                design_url="https://canva.com/design/test-invalid",
                config=config,
            )
