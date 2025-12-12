import logging

from fastapi import APIRouter, HTTPException, Query

from app.schemas.canva import (
    CanvaDesignResponse,
    CreateDesignRequest,
    ExportRequest,
    ExportResponse,
    ModifyDesignRequest,
    TemplateSearchResponse,
)
from app.services.canva_service import canva_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/create", response_model=CanvaDesignResponse)
async def create_design(
    request: CreateDesignRequest,
) -> CanvaDesignResponse:
    """
    Create a new Canva design using MCP.
    """
    try:
        result = await canva_service.create_design(
            design_type=request.design_type,
            title=request.title,
            elements=request.elements,
            style=request.style,
        )
        return result
    except Exception as e:
        logger.error(f"Failed to create design: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/modify", response_model=CanvaDesignResponse)
async def modify_design(
    request: ModifyDesignRequest,
) -> CanvaDesignResponse:
    """
    Modify an existing Canva design or template.
    """
    try:
        result = await canva_service.modify_design(
            design_id=request.design_id,
            modifications=request.modifications,
        )
        return result
    except Exception as e:
        logger.error(f"Failed to modify design: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/templates", response_model=TemplateSearchResponse)
async def search_templates(
    query: str = Query(..., description="Search query for templates"),
    design_type: str | None = Query(None, description="Filter by design type"),
    limit: int = Query(10, le=50, description="Number of results to return"),
) -> TemplateSearchResponse:
    """
    Search Canva templates by query.
    """
    try:
        templates = await canva_service.search_templates(
            query=query,
            design_type=design_type,
            limit=limit,
        )
        return TemplateSearchResponse(
            templates=templates,  # type: ignore
            total_count=len(templates),
        )
    except Exception as e:
        logger.error(f"Failed to search templates: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/export/{design_id}", response_model=ExportResponse)
async def export_design(
    design_id: str,
    request: ExportRequest,
) -> ExportResponse:
    """
    Export a Canva design to PDF, PNG, or JPG.
    """
    try:
        result = await canva_service.export_design(
            design_id=design_id,
            format=request.format.value,
            quality=request.quality.value,
        )

        return ExportResponse(
            url=result.get("url", ""),
            format=result.get("format", request.format.value),
            file_size=result.get("file_size"),
            expires_at=result.get("expires_at"),
        )
    except Exception as e:
        logger.error(f"Failed to export design: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
