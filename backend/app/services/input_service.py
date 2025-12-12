import logging
from pathlib import Path

from app.core.config import get_settings
from app.schemas.input import (
    ImageUploadResponse,
)
from app.utils.image_utils import (
    fetch_image_from_url,
    generate_file_hash,
    get_image_dimensions,
    get_mime_type,
    validate_image,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class InputService:
    """Service for handling file uploads and input processing."""

    def __init__(self) -> None:
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = settings.upload_max_size_mb * 1024 * 1024
        self.allowed_types = settings.upload_allowed_types

    async def save_uploaded_file(
        self,
        file_content: bytes,
        original_filename: str,
        session_id: str,
    ) -> ImageUploadResponse:
        """Save uploaded file and return response."""
        is_valid, error = validate_image(
            file_content, self.allowed_types, self.max_size_bytes
        )
        if not is_valid:
            raise ValueError(error or "Invalid image")

        mime_type = get_mime_type(file_content)
        if not mime_type:
            raise ValueError("Could not determine image type")

        dimensions = get_image_dimensions(file_content)
        file_hash = generate_file_hash(file_content)
        extension = mime_type.split("/")[1]
        filename = f"{session_id}_{file_hash}.{extension}"

        file_path = self.upload_dir / filename
        file_path.write_bytes(file_content)

        url = f"{settings.upload_url_base}/{filename}"

        return ImageUploadResponse(
            url=url,
            mime_type=mime_type,
            dimensions=dimensions,
            file_size=len(file_content),
            original_filename=original_filename,
        )

    async def fetch_and_save_from_url(
        self,
        image_url: str,
        session_id: str,
    ) -> ImageUploadResponse:
        """Fetch image from URL and save it."""
        try:
            content, mime_type = await fetch_image_from_url(image_url)
        except Exception as e:
            logger.error(f"Failed to fetch image from URL: {e}")
            raise ValueError(f"Failed to fetch image: {str(e)}") from e

        is_valid, error = validate_image(
            content, self.allowed_types, self.max_size_bytes
        )
        if not is_valid:
            raise ValueError(error or "Invalid image")

        dimensions = get_image_dimensions(content)
        file_hash = generate_file_hash(content)
        extension = mime_type.split("/")[1]
        filename = f"{session_id}_{file_hash}.{extension}"

        file_path = self.upload_dir / filename
        file_path.write_bytes(content)

        url = f"{settings.upload_url_base}/{filename}"

        return ImageUploadResponse(
            url=url,
            mime_type=mime_type,
            dimensions=dimensions,
            file_size=len(content),
            original_filename=None,
        )

    def cleanup_session_files(self, session_id: str) -> int:
        """Clean up files for a session. Returns number of files deleted."""
        count = 0
        for file_path in self.upload_dir.glob(f"{session_id}_*"):
            try:
                file_path.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {file_path}: {e}")
        return count


input_service: InputService = InputService()
