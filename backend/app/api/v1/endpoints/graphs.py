from datetime import UTC, datetime

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, status

from app.models.graph import Graph
from app.schemas.graph import GraphCreate, GraphResponse, GraphUpdate

router = APIRouter()


def _graph_to_response(graph: Graph) -> GraphResponse:
    """Convert Graph document to response schema."""
    return GraphResponse(
        id=str(graph.id),
        name=graph.name,
        description=graph.description,
        nodes=graph.nodes,
        edges=graph.edges,
        created_at=graph.created_at,
        updated_at=graph.updated_at,
    )


@router.post(
    "",
    response_model=GraphResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create graph",
    description="Create a new graph configuration.",
)
async def create_graph(data: GraphCreate) -> GraphResponse:
    """Create a new graph."""
    graph = Graph(
        name=data.name,
        description=data.description,
        nodes=data.nodes,
        edges=data.edges,
    )
    await graph.insert()
    return _graph_to_response(graph)


@router.get(
    "",
    response_model=list[GraphResponse],
    summary="List graphs",
    description="Get all graph configurations.",
)
async def list_graphs() -> list[GraphResponse]:
    """Get all graphs."""
    graphs = await Graph.find_all().to_list()
    return [_graph_to_response(g) for g in graphs]


@router.get(
    "/{graph_id}",
    response_model=GraphResponse,
    summary="Get graph",
    description="Get a graph by ID.",
)
async def get_graph(graph_id: str) -> GraphResponse:
    """Get a graph by ID."""
    graph = await Graph.get(PydanticObjectId(graph_id))
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Graph not found",
        )
    return _graph_to_response(graph)


@router.patch(
    "/{graph_id}",
    response_model=GraphResponse,
    summary="Update graph",
    description="Update a graph by ID.",
)
async def update_graph(graph_id: str, data: GraphUpdate) -> GraphResponse:
    """Update a graph by ID."""
    graph = await Graph.get(PydanticObjectId(graph_id))
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Graph not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.now(UTC)
        await graph.set(update_data)

    return _graph_to_response(graph)


@router.delete(
    "/{graph_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete graph",
    description="Delete a graph by ID.",
)
async def delete_graph(graph_id: str) -> None:
    """Delete a graph by ID."""
    graph = await Graph.get(PydanticObjectId(graph_id))
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Graph not found",
        )
    await graph.delete()
