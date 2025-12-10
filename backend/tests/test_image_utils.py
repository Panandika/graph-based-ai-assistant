import pytest

from app.utils.image_utils import (
    encode_to_base64,
    generate_file_hash,
    get_image_dimensions,
    get_mime_type,
    validate_image,
)


class TestImageUtils:
    """Test image utility functions."""

    def test_get_mime_type_png(self):
        """Test PNG MIME type detection."""
        png_header = b"\x89PNG\r\n\x1a\n"
        mime = get_mime_type(png_header)
        assert mime == "image/png"

    def test_get_mime_type_jpeg(self):
        """Test JPEG MIME type detection."""
        jpeg_header = b"\xff\xd8\xff"
        mime = get_mime_type(jpeg_header)
        assert mime == "image/jpeg"

    def test_get_mime_type_webp(self):
        """Test WebP MIME type detection."""
        webp_header = b"RIFF\x00\x00\x00\x00WEBP"
        mime = get_mime_type(webp_header)
        assert mime == "image/webp"

    def test_get_mime_type_gif(self):
        """Test GIF MIME type detection."""
        gif_header = b"GIF89a"
        mime = get_mime_type(gif_header)
        assert mime == "image/gif"

    def test_get_mime_type_unknown(self):
        """Test unknown file type returns None."""
        unknown = b"unknown file content"
        mime = get_mime_type(unknown)
        assert mime is None

    def test_get_image_dimensions_png(self):
        """Test PNG dimension extraction."""
        png_data = (
            b"\x89PNG\r\n\x1a\n"
            + b"\x00\x00\x00\rIHDR"
            + b"\x00\x00\x01\x90"  # width: 400
            + b"\x00\x00\x01\x2c"  # height: 300
            + b"\x00" * 100
        )
        dims = get_image_dimensions(png_data)
        assert dims is not None
        assert dims.width == 400
        assert dims.height == 300

    def test_get_image_dimensions_invalid(self):
        """Test dimension extraction with invalid data."""
        invalid_data = b"not an image"
        dims = get_image_dimensions(invalid_data)
        assert dims is None

    def test_generate_file_hash(self):
        """Test file hash generation."""
        content1 = b"test content"
        content2 = b"test content"
        content3 = b"different content"

        hash1 = generate_file_hash(content1)
        hash2 = generate_file_hash(content2)
        hash3 = generate_file_hash(content3)

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 16

    def test_encode_to_base64(self):
        """Test base64 encoding."""
        content = b"test data"
        encoded = encode_to_base64(content)

        assert isinstance(encoded, str)
        assert len(encoded) > 0

        import base64

        decoded = base64.b64decode(encoded)
        assert decoded == content

    def test_validate_image_valid_png(self):
        """Test validating a valid PNG image."""
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        allowed_types = ["image/png", "image/jpeg"]
        max_size = 1024 * 1024

        is_valid, error = validate_image(png_data, allowed_types, max_size)

        assert is_valid is True
        assert error is None

    def test_validate_image_too_large(self):
        """Test validating oversized image."""
        large_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 1000
        allowed_types = ["image/png"]
        max_size = 500

        is_valid, error = validate_image(large_data, allowed_types, max_size)

        assert is_valid is False
        assert "exceeds maximum" in error

    def test_validate_image_wrong_type(self):
        """Test validating image with disallowed type."""
        gif_data = b"GIF89a" + b"\x00" * 100
        allowed_types = ["image/png", "image/jpeg"]
        max_size = 1024 * 1024

        is_valid, error = validate_image(gif_data, allowed_types, max_size)

        assert is_valid is False
        assert "not allowed" in error

    def test_validate_image_unknown_type(self):
        """Test validating file with unknown type."""
        unknown_data = b"unknown" + b"\x00" * 100
        allowed_types = ["image/png"]
        max_size = 1024 * 1024

        is_valid, error = validate_image(unknown_data, allowed_types, max_size)

        assert is_valid is False
        assert "Could not determine file type" in error
