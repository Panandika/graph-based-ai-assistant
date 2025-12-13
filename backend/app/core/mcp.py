import logging
from pathlib import Path
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
        self._canva_token: str | None = None
        self._token_file = Path("canva_token.txt")

    def _load_token(self) -> None:
        if self._token_file.exists():
            try:
                self._canva_token = self._token_file.read_text().strip()
            except Exception as e:
                logger.error(f"Failed to read Canva token: {e}")

    async def set_canva_token(self, token: str) -> None:
        """Set Canva token and reload client."""
        self._canva_token = token
        try:
            self._token_file.write_text(token)
        except Exception as e:
            logger.error(f"Failed to write Canva token: {e}")

        # Reload to apply new token
        await self.shutdown()
        await self.initialize()

    def has_canva_token(self) -> bool:
        return bool(self._canva_token)

    async def initialize(self) -> None:
        """Initialize the MCP client and load tools from all servers."""
        if self._initialized:
            return

        self._load_token()

        # Dynamic config based on auth state
        config = {}
        if self._canva_token:
            config["canva"] = {
                "transport": "sse",
                "url": "https://mcp.canva.com/mcp",
                "headers": {"Authorization": f"Bearer {self._canva_token}"},
            }
        else:
            logger.info("No Canva token found. Canva tools will not be loaded.")

        if not config:
            logger.info("No MCP servers configured.")
            self._initialized = True  # Mark as initialized even if empty
            return

        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient

            self._client = MultiServerMCPClient(config)  # type: ignore
            await self._client.connect()  # Ensure connection is made
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
            # MultiServerMCPClient might need explicit close if supported,
            # otherwise just dereference
            try:
                # Check if it has a close/shutdown method
                if hasattr(self._client, "close"):
                    await self._client.close()
            except Exception as e:
                logger.warning(f"Error closing MCP client: {e}")

            self._client = None
            self._tools = []
            self._initialized = False
            logger.info("MCP client shut down")


mcp_manager: MCPClientManager = MCPClientManager()


async def get_mcp_tools() -> list[BaseTool]:
    """FastAPI dependency for getting MCP tools."""
    return await mcp_manager.get_tools()
