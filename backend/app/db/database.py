from typing import Any, cast

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings

_client: AsyncIOMotorClient[Any] | None = None


async def init_db() -> None:
    """Initialize MongoDB connection and Beanie ODM."""
    global _client
    settings = get_settings()

    _client = AsyncIOMotorClient(settings.mongodb_url)
    database: AsyncIOMotorDatabase[Any] = _client[settings.database_name]

    from app.models.graph import Graph
    from app.models.workflow import Thread, Workflow

    await init_beanie(
        database=cast(Any, database),
        document_models=[Workflow, Graph, Thread],
    )


async def close_db() -> None:
    """Close MongoDB connection."""
    global _client
    if _client:
        _client.close()
        _client = None


def get_client() -> AsyncIOMotorClient[Any]:
    """Get the MongoDB client instance."""
    if _client is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _client
