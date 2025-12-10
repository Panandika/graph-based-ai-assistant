from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CanvaOperation(str, Enum):
    CREATE = "create"
    MODIFY = "modify"


class CanvaOutputFormat(str, Enum):
    PDF = "pdf"
    PNG = "png"
    JPG = "jpg"
    LINK = "link"


class TemplateSource(str, Enum):
    SEARCH = "search"
    ID = "id"
    FROM_INPUT = "from_input"


class ExportQuality(str, Enum):
    STANDARD = "standard"
    HIGH = "high"


class CanvaMCPNodeConfig(BaseModel):
    """Configuration for Canva MCP node."""

    operation: CanvaOperation = CanvaOperation.CREATE
    template_source: TemplateSource = TemplateSource.FROM_INPUT
    template_id: str | None = None
    template_search_query: str | None = None
    design_name: str | None = None
    brand_kit_id: str | None = None
    output_format: CanvaOutputFormat = CanvaOutputFormat.LINK
    export_quality: ExportQuality = ExportQuality.STANDARD
    timeout: int = 30000


class CanvaElement(BaseModel):
    """A Canva design element."""

    type: str
    content: str | None = None
    style: dict[str, Any] | None = None


class StylePreferences(BaseModel):
    """Style preferences for Canva design."""

    color_scheme: str | None = None
    font_style: str | None = None
    mood: str | None = None


class CanvaInstructions(BaseModel):
    """Instructions for Canva design creation/modification."""

    action: CanvaOperation
    design_type: str
    template_query: str | None = None
    elements: list[CanvaElement] = Field(default_factory=list)
    style_preferences: StylePreferences | None = None


class CreateDesignRequest(BaseModel):
    """Request to create a new Canva design."""

    design_type: str
    title: str
    elements: list[dict[str, Any]] = Field(default_factory=list)
    style: dict[str, Any] | None = None


class ModifyDesignRequest(BaseModel):
    """Request to modify an existing design."""

    design_id: str
    modifications: list[dict[str, Any]]


class TemplateSearchRequest(BaseModel):
    """Request to search for templates."""

    query: str
    design_type: str | None = None
    limit: int = Field(default=10, le=50)


class ExportRequest(BaseModel):
    """Request to export a design."""

    format: CanvaOutputFormat
    quality: ExportQuality = ExportQuality.STANDARD


class CanvaDesignResponse(BaseModel):
    """Response from Canva design operations."""

    success: bool
    design_id: str
    design_url: str
    export_url: str | None = None
    export_format: str | None = None
    thumbnail_url: str | None = None
    error: str | None = None


class CanvaTemplate(BaseModel):
    """A Canva template."""

    id: str
    title: str
    thumbnail_url: str
    design_type: str


class TemplateSearchResponse(BaseModel):
    """Response from template search."""

    templates: list[CanvaTemplate]
    total_count: int


class ExportResponse(BaseModel):
    """Response from design export."""

    url: str
    format: str
    file_size: int | None = None
    expires_at: str | None = None
