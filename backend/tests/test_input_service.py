from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.input_service import InputService


@pytest.fixture
def input_service():
    """Create input service instance for testing."""
    service = InputService()
    service.upload_dir.mkdir(parents=True, exist_ok=True)
    yield service
    for file in service.upload_dir.glob("*"):
        file.unlink()


class TestInputService:
    """Test input service file handling."""

    @pytest.mark.asyncio
    async def test_save_uploaded_file_png(self, input_service):
        """Test saving a PNG file."""
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        session_id = "test-session"
        filename = "test.png"

        result = await input_service.save_uploaded_file(
            png_header, filename, session_id
        )

        assert result.url.endswith(".png")
        assert result.mime_type == "image/png"
        assert result.file_size == len(png_header)
        assert result.original_filename == filename

    @pytest.mark.asyncio
    async def test_save_uploaded_file_exceeds_size(self, input_service):
        """Test file size validation."""
        large_content = b"x" * (input_service.max_size_bytes + 1)
        session_id = "test-session"

        with pytest.raises(ValueError, match="exceeds maximum"):
            await input_service.save_uploaded_file(
                large_content, "large.png", session_id
            )

    @pytest.mark.asyncio
    async def test_save_uploaded_file_invalid_type(self, input_service):
        """Test file type validation."""
        txt_content = b"Just some text"
        session_id = "test-session"

        with pytest.raises(ValueError, match="not allowed"):
            await input_service.save_uploaded_file(
                txt_content, "test.txt", session_id
            )

    @pytest.mark.asyncio
    @patch("app.services.input_service.fetch_image_from_url")
    async def test_fetch_and_save_from_url(self, mock_fetch, input_service):
        """Test fetching and saving image from URL."""
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        mock_fetch.return_value = (png_header, "image/png")

        session_id = "test-session"
        url = "https://example.com/image.png"

        result = await input_service.fetch_and_save_from_url(url, session_id)

        assert result.mime_type == "image/png"
        assert result.file_size == len(png_header)
        assert result.url.startswith("http")
        mock_fetch.assert_called_once_with(url)

    @pytest.mark.asyncio
    @patch("app.services.input_service.fetch_image_from_url")
    async def test_fetch_from_url_network_error(self, mock_fetch, input_service):
        """Test handling network errors when fetching from URL."""
        mock_fetch.side_effect = Exception("Network error")

        session_id = "test-session"
        url = "https://example.com/image.png"

        with pytest.raises(ValueError, match="Failed to fetch image"):
            await input_service.fetch_and_save_from_url(url, session_id)

    def test_cleanup_session_files(self, input_service):
        """Test cleaning up files for a session."""
        session_id = "test-session"

        file1 = input_service.upload_dir / f"{session_id}_file1.png"
        file2 = input_service.upload_dir / f"{session_id}_file2.jpg"
        file3 = input_service.upload_dir / "other_session_file.png"

        file1.write_bytes(b"content1")
        file2.write_bytes(b"content2")
        file3.write_bytes(b"content3")

        count = input_service.cleanup_session_files(session_id)

        assert count == 2
        assert not file1.exists()
        assert not file2.exists()
        assert file3.exists()
