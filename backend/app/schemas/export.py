from enum import Enum

from pydantic import BaseModel, Field


class OutputType(str, Enum):
    PDF = "pdf"
    IMAGE = "image"
    LINK = "link"


class PageSize(str, Enum):
    A4 = "A4"
    LETTER = "Letter"
    ORIGINAL = "Original"


class PDFQuality(str, Enum):
    STANDARD = "standard"
    PRINT = "print"


class ImageFormat(str, Enum):
    PNG = "png"
    JPG = "jpg"
    WEBP = "webp"


class AccessLevel(str, Enum):
    VIEW = "view"
    EDIT = "edit"


class PDFOptions(BaseModel):
    """PDF export options."""

    page_size: PageSize = PageSize.ORIGINAL
    quality: PDFQuality = PDFQuality.STANDARD


class ImageOptions(BaseModel):
    """Image export options."""

    format: ImageFormat = ImageFormat.PNG
    quality: int = Field(default=85, ge=1, le=100)
    scale: float = Field(default=1.0, ge=0.5, le=4.0)


class LinkOptions(BaseModel):
    """Link sharing options."""

    access_level: AccessLevel = AccessLevel.VIEW
    expires_in: int | None = Field(default=None, description="Hours until expiry")


class OutputExportNodeConfig(BaseModel):
    """Configuration for output export node."""

    output_type: OutputType = OutputType.LINK
    pdf_options: PDFOptions | None = None
    image_options: ImageOptions | None = None
    link_options: LinkOptions | None = None
    download_automatically: bool = False
    show_preview: bool = True


class OutputExportResult(BaseModel):
    """Result from output export."""

    output_type: OutputType
    url: str
    filename: str | None = None
    file_size: int | None = None
    preview_url: str | None = None
    canva_edit_url: str
    expires_at: str | None = None
