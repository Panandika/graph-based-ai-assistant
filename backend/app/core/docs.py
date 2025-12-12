API_TITLE = "Graph AI Assistant API"
API_DESCRIPTION = """
This API allows for graph-based AI workflow orchestration with LangGraph.

## Features

* **Workflows**: Create and execute complex AI workflows.
* **Graphs**: Manage graph structures with nodes and edges.
* **Canva Integration**: Interact with Canva via MCP.
* **Uploads**: Manage file uploads.
* **Health**: Check system status.
"""
API_VERSION = "0.1.0"

tags_metadata = [
    {
        "name": "workflows",
        "description": "Operations with workflows and executions.",
    },
    {
        "name": "graphs",
        "description": "Manage graph definitions (nodes, edges).",
    },
    {
        "name": "canva",
        "description": "Canva integration endpoints.",
    },
    {
        "name": "uploads",
        "description": "File upload and management.",
    },
    {
        "name": "health",
        "description": "Health check endpoints.",
    },
]
