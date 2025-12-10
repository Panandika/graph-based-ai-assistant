import logging
import uuid

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.schemas.input import ImageUploadRequest, ImageUploadResponse
from app.services.input_service import input_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/image", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    session_id: str = Query(default_factory=lambda: str(uuid.uuid4())),
) -> ImageUploadResponse:
    """
    Upload an image file and return accessible URL.
    The file will be stored temporarily and associated with the session.
    """
    try:
        content = await file.read()
        result = await input_service.save_uploaded_file(
            content,
            original_filename=file.filename or "unknown",
            session_id=session_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to upload image: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload image")


@router.post("/image-url", response_model=ImageUploadResponse)
async def upload_image_from_url(
    request: ImageUploadRequest,
) -> ImageUploadResponse:
    """
    Fetch an image from a URL and store it locally.
    Validates the URL and checks file size/type.
    """
    try:
        result = await input_service.fetch_and_save_from_url(
            image_url=str(request.url),
            session_id=request.session_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch image from URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch image")


@router.delete("/session/{session_id}")
async def cleanup_session(session_id: str) -> dict[str, int]:
    """
    Clean up all files associated with a session.
    Returns the number of files deleted.
    """
    try:
        count = input_service.cleanup_session_files(session_id)
        return {"deleted_count": count}
    except Exception as e:
        logger.error(f"Failed to cleanup session: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup session")
