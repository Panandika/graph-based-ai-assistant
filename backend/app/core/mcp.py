import logging
from typing import Any

from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

MCP_SERVERS_CONFIG = {
    "canva": {
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@canva/cli@latest", "mcp"],
    },
}


class MCPClientManager:
    """
    Manages MCP client connections using langchain-mcp-adapters.
    Provides tools that can be used directly with LangGraph agents.
    """

    def __init__(self) -> None:
        self._client: Any = None
        self._tools: list[BaseTool] = []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the MCP client and load tools from all servers."""
        if self._initialized:
            return

        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient

            self._client = MultiServerMCPClient(MCP_SERVERS_CONFIG)  # type: ignore
            self._tools = await self._client.get_tools()
            self._initialized = True
            logger.info(f"MCP client initialized with {len(self._tools)} tools")
        except ImportError as e:
            logger.error(
                f"langchain-mcp-adapters not installed: {e}. "
                "Run: uv add langchain-mcp-adapters"
            )
            self._tools = []
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")
            self._tools = []

    async def get_tools(self) -> list[BaseTool]:
        """Get all loaded MCP tools as LangChain tools."""
        if not self._initialized:
            await self.initialize()
        return self._tools

    async def get_canva_tools(self) -> list[BaseTool]:
        """Get only Canva-related tools."""
        all_tools = await self.get_tools()
        return [t for t in all_tools if "canva" in t.name.lower()]

    async def shutdown(self) -> None:
        """Cleanup MCP client connections."""
        if self._client:
            self._client = None
            self._tools = []
            self._initialized = False
            logger.info("MCP client shut down")


mcp_manager: MCPClientManager = MCPClientManager()


async def get_mcp_tools() -> list[BaseTool]:
    """FastAPI dependency for getting MCP tools."""
    return await mcp_manager.get_tools()
