from datetime import UTC, datetime

from beanie import PydanticObjectId
from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.models.workflow import Thread, ThreadStatus, Workflow
from app.schemas.workflow import (
    ExecuteWorkflowRequest,
    ExecuteWorkflowResponse,
    ThreadResponse,
    WorkflowCreate,
    WorkflowResponse,
    WorkflowUpdate,
)
from app.services import workflow_service

router = APIRouter()


def _workflow_to_response(workflow: Workflow) -> WorkflowResponse:
    """Convert Workflow document to response schema."""
    return WorkflowResponse(
        id=str(workflow.id),
        name=workflow.name,
        description=workflow.description,
        status=workflow.status,
        graph_id=workflow.graph_id,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


def _thread_to_response(thread: Thread) -> ThreadResponse:
    """Convert Thread document to response schema."""
    return ThreadResponse(
        id=str(thread.id),
        workflow_id=thread.workflow_id,
        status=thread.status,
        current_node=thread.current_node,
        input_data=thread.input_data,
        output_data=thread.output_data,
        error_message=thread.error_message,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
    )


@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create workflow",
    description="Create a new workflow definition.",
)
async def create_workflow(data: WorkflowCreate) -> WorkflowResponse:
    """Create a new workflow."""
    workflow = Workflow(
        name=data.name,
        description=data.description,
        graph_id=data.graph_id,
    )
    await workflow.insert()
    return _workflow_to_response(workflow)


@router.get(
    "",
    response_model=list[WorkflowResponse],
    summary="List workflows",
    description="Get all workflows.",
)
async def list_workflows() -> list[WorkflowResponse]:
    """Get all workflows."""
    workflows = await Workflow.find_all().to_list()
    return [_workflow_to_response(w) for w in workflows]


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Get workflow",
    description="Get a workflow by ID.",
)
async def get_workflow(workflow_id: str) -> WorkflowResponse:
    """Get a workflow by ID."""
    workflow = await Workflow.get(PydanticObjectId(workflow_id))
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    return _workflow_to_response(workflow)


@router.patch(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Update workflow",
    description="Update a workflow by ID.",
)
async def update_workflow(workflow_id: str, data: WorkflowUpdate) -> WorkflowResponse:
    """Update a workflow by ID."""
    workflow = await Workflow.get(PydanticObjectId(workflow_id))
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.now(UTC)
        await workflow.set(update_data)

    return _workflow_to_response(workflow)


@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete workflow",
    description="Delete a workflow by ID.",
)
async def delete_workflow(workflow_id: str) -> None:
    """Delete a workflow by ID."""
    workflow = await Workflow.get(PydanticObjectId(workflow_id))
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    await workflow.delete()


@router.post(
    "/{workflow_id}/execute",
    response_model=ExecuteWorkflowResponse,
    summary="Execute workflow",
    description="Start a new execution thread for a workflow.",
)
async def execute_workflow(
    workflow_id: str,
    data: ExecuteWorkflowRequest,
    background_tasks: BackgroundTasks,
) -> ExecuteWorkflowResponse:
    """Execute a workflow by creating a new thread."""
    workflow = await Workflow.get(PydanticObjectId(workflow_id))
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    thread = Thread(
        workflow_id=str(workflow.id),
        status=ThreadStatus.PENDING,
        input_data=data.input_data,
    )
    await thread.insert()

    background_tasks.add_task(workflow_service.execute_workflow, str(thread.id))

    return ExecuteWorkflowResponse(
        thread_id=str(thread.id),
        status=thread.status,
    )


@router.get(
    "/{workflow_id}/threads",
    response_model=list[ThreadResponse],
    summary="List workflow threads",
    description="Get all execution threads for a workflow.",
)
async def list_workflow_threads(workflow_id: str) -> list[ThreadResponse]:
    """Get all threads for a workflow."""
    threads = await Thread.find(Thread.workflow_id == workflow_id).to_list()
    return [_thread_to_response(t) for t in threads]


@router.get(
    "/{workflow_id}/threads/{thread_id}",
    response_model=ThreadResponse,
    summary="Get thread status",
    description="Get the status of a specific execution thread.",
)
async def get_thread_status(workflow_id: str, thread_id: str) -> ThreadResponse:
    """Get thread status."""
    thread = await Thread.get(PydanticObjectId(thread_id))
    if not thread or thread.workflow_id != workflow_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )
    return _thread_to_response(thread)
