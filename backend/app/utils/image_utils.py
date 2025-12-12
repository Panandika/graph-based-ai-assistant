import base64
import hashlib
import logging

import httpx

from app.schemas.input import ImageDimensions

logger = logging.getLogger(__name__)


def get_image_dimensions(file_content: bytes) -> ImageDimensions | None:
    """Extract image dimensions from file content without external dependencies."""
    try:
        if file_content[:8] == b"\x89PNG\r\n\x1a\n":
            width = int.from_bytes(file_content[16:20], "big")
            height = int.from_bytes(file_content[20:24], "big")
            return ImageDimensions(width=width, height=height)

        if file_content[:2] == b"\xff\xd8":
            offset = 2
            while offset < len(file_content):
                marker = file_content[offset : offset + 2]
                if marker[0] != 0xFF:
                    break
                if marker[1] in (0xC0, 0xC2):
                    height = int.from_bytes(
                        file_content[offset + 5 : offset + 7], "big"
                    )
                    width = int.from_bytes(file_content[offset + 7 : offset + 9], "big")
                    return ImageDimensions(width=width, height=height)
                length = int.from_bytes(file_content[offset + 2 : offset + 4], "big")
                offset += 2 + length

        if file_content[:4] == b"RIFF" and file_content[8:12] == b"WEBP":
            chunk_type = file_content[12:16]
            if chunk_type == b"VP8 ":
                width = int.from_bytes(file_content[26:28], "little") & 0x3FFF
                height = int.from_bytes(file_content[28:30], "little") & 0x3FFF
                return ImageDimensions(width=width, height=height)
            elif chunk_type == b"VP8L":
                bits = int.from_bytes(file_content[21:25], "little")
                width = (bits & 0x3FFF) + 1
                height = ((bits >> 14) & 0x3FFF) + 1
                return ImageDimensions(width=width, height=height)

        if file_content[:6] in (b"GIF87a", b"GIF89a"):
            width = int.from_bytes(file_content[6:8], "little")
            height = int.from_bytes(file_content[8:10], "little")
            return ImageDimensions(width=width, height=height)

    except (IndexError, ValueError) as e:
        logger.warning(f"Failed to extract image dimensions: {e}")

    return None


def get_mime_type(file_content: bytes) -> str | None:
    """Detect MIME type from file content."""
    if file_content[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if file_content[:2] == b"\xff\xd8":
        return "image/jpeg"
    if file_content[:4] == b"RIFF" and file_content[8:12] == b"WEBP":
        return "image/webp"
    if file_content[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    return None


def generate_file_hash(file_content: bytes) -> str:
    """Generate SHA-256 hash of file content."""
    return hashlib.sha256(file_content).hexdigest()[:16]


def encode_to_base64(file_content: bytes) -> str:
    """Encode file content to base64 string."""
    return base64.b64encode(file_content).decode("utf-8")


def decode_from_base64(base64_string: str) -> bytes:
    """Decode base64 string to bytes."""
    return base64.b64decode(base64_string)


async def fetch_image_from_url(url: str, timeout: float = 30.0) -> tuple[bytes, str]:
    """
    Fetch image from URL.

    Returns tuple of (content_bytes, mime_type).
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()

        content = response.content
        content_type = response.headers.get("content-type", "")

        if ";" in content_type:
            content_type = content_type.split(";")[0].strip()

        mime_type = content_type or get_mime_type(content)
        if not mime_type:
            raise ValueError("Could not determine image MIME type")

        return content, mime_type


def validate_image(
    content: bytes,
    allowed_types: list[str],
    max_size_bytes: int,
) -> tuple[bool, str | None]:
    """
    Validate image content.

    Returns (is_valid, error_message).
    """
    if len(content) > max_size_bytes:
        return (
            False,
            f"File size exceeds maximum of {max_size_bytes // (1024 * 1024)}MB",
        )

    mime_type = get_mime_type(content)
    if not mime_type:
        return False, "Could not determine file type"

    if mime_type not in allowed_types:
        return False, f"File type {mime_type} not allowed"

    return True, None
