import logging
from datetime import UTC, datetime

from beanie import PydanticObjectId

from app.models.graph import Graph
from app.models.workflow import Thread, ThreadStatus, Workflow
from app.services.graph_service import GraphExecutor

logger = logging.getLogger(__name__)


async def execute_workflow(thread_id: str) -> None:
    """
    Execute a workflow thread asynchronously.

    This function is designed to be run as a background task.
    """
    thread = await Thread.get(PydanticObjectId(thread_id))
    if not thread:
        logger.error(f"Thread {thread_id} not found")
        return

    workflow = await Workflow.get(PydanticObjectId(thread.workflow_id))
    if not workflow:
        logger.error(f"Workflow {thread.workflow_id} not found")
        thread.status = ThreadStatus.FAILED
        thread.error_message = "Workflow not found"
        thread.updated_at = datetime.now(UTC)
        await thread.save()
        return

    if not workflow.graph_id:
        logger.error(f"Workflow {workflow.id} has no graph")
        thread.status = ThreadStatus.FAILED
        thread.error_message = "Workflow has no graph configuration"
        thread.updated_at = datetime.now(UTC)
        await thread.save()
        return

    graph = await Graph.get(PydanticObjectId(workflow.graph_id))
    if not graph:
        logger.error(f"Graph {workflow.graph_id} not found")
        thread.status = ThreadStatus.FAILED
        thread.error_message = "Graph not found"
        thread.updated_at = datetime.now(UTC)
        await thread.save()
        return

    thread.status = ThreadStatus.RUNNING
    thread.updated_at = datetime.now(UTC)
    await thread.save()

    try:
        executor = GraphExecutor(graph)
        executor.compile()

        result = await executor.execute(
            thread_id=str(thread.id),
            input_data=thread.input_data,
        )

        thread.status = ThreadStatus.COMPLETED
        thread.output_data = result
        thread.updated_at = datetime.now(UTC)
        await thread.save()

    except Exception as e:
        logger.exception(f"Error executing workflow: {e}")
        thread.status = ThreadStatus.FAILED
        thread.error_message = str(e)
        thread.updated_at = datetime.now(UTC)
        await thread.save()
