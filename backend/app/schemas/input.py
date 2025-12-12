from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class InputSource(str, Enum):
    UPLOAD = "upload"
    URL = "url"
    CLIPBOARD = "clipboard"


class InputTextNodeConfig(BaseModel):
    """Configuration for text input node."""

    placeholder: str | None = None
    max_length: int | None = None
    required: bool = True
    default_value: str | None = None


class InputImageNodeConfig(BaseModel):
    """Configuration for image input node."""

    allow_upload: bool = True
    allow_url: bool = True
    allow_clipboard: bool = True
    max_file_size_mb: int = 10
    accepted_formats: list[str] = Field(
        default_factory=lambda: ["image/png", "image/jpeg", "image/webp"]
    )


class InputCombinedNodeConfig(BaseModel):
    """Configuration for combined text and image input node."""

    text_config: InputTextNodeConfig = Field(default_factory=InputTextNodeConfig)
    image_config: InputImageNodeConfig = Field(default_factory=InputImageNodeConfig)
    image_required: bool = False
    text_required: bool = True


class TextInputOutput(BaseModel):
    """Output from text input node."""

    text: str
    char_count: int
    timestamp: str | None = None


class ImageDimensions(BaseModel):
    """Image dimensions."""

    width: int
    height: int


class ImageInputOutput(BaseModel):
    """Output from image input node."""

    source: InputSource
    image_url: str
    base64: str | None = None
    mime_type: str
    dimensions: ImageDimensions | None = None


class CombinedInputOutput(BaseModel):
    """Output from combined input node."""

    text: TextInputOutput | None = None
    image: ImageInputOutput | None = None


class ImageUploadRequest(BaseModel):
    """Request for uploading image from URL."""

    url: HttpUrl
    session_id: str


class ImageUploadResponse(BaseModel):
    """Response from image upload."""

    url: str
    mime_type: str
    dimensions: ImageDimensions | None = None
    file_size: int
    original_filename: str | None = None
