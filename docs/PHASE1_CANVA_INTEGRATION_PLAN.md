# Phase 1: Input-to-Canva Pipeline Implementation Plan

## Overview

This document outlines the implementation plan for the core feature: a graph-based pipeline that accepts user input (image/text), processes it through an LLM, sends instructions to Canva via MCP, and returns the design output.

### Feature Summary

```
[Input Node] → [LLM Node] → [Canva MCP Node] → [Output Node]
     ↓              ↓              ↓                ↓
  Image/Text    Transform &    Create/Edit      PDF/Link/Image
               Generate Prompt   Design
```

### Key Requirements

| Requirement | Details |
|-------------|---------|
| Input Types | Image upload, image URL, clipboard paste, free-form text |
| LLM Function | Transform/enhance text, generate Canva design instructions |
| LLM Customization | User can customize prompt template per node |
| Canva Operations | Create new design, modify existing templates |
| Output Formats | PDF export, editable Canva link, image export |
| Output Selection | User selects format upfront (before execution) |
| Node Architecture | Separate nodes for each step |
| Branching | Support multiple outputs from single LLM node |

---

## Architecture Design

### New Node Types

Extending the existing node types (`start`, `llm`, `tool`, `condition`, `end`), we introduce:

| Node Type | Purpose | Inputs | Outputs |
|-----------|---------|--------|---------|
| `input_text` | Accept free-form text input | User text | `text: string` |
| `input_image` | Accept image (upload/URL/paste) | Image data | `image_url: string`, `image_base64?: string` |
| `input_combined` | Accept both text and image | User text + image | `text: string`, `image_url: string` |
| `llm_transform` | Enhanced LLM node with vision | Text/Image | `transformed_text: string`, `canva_instructions: object` |
| `canva_mcp` | Canva MCP tool node | Instructions | `design_id: string`, `design_url: string` |
| `output_export` | Export Canva design | Design reference | PDF/Image/Link |

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │ Input Node   │───▶│ LLM Node     │───▶│ Canva Node   │───▶│Output Node │ │
│  │ (Text/Image) │    │ (Transform)  │    │ (MCP Tool)   │    │ (Export)   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └────────────┘ │
│         │                   │                   │                   │        │
│         ▼                   ▼                   ▼                   ▼        │
│  ┌──────────────────────────────────────────────────────────────────────────┤
│  │                    Zustand Store (Graph State)                           │
│  └──────────────────────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼ REST API
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (FastAPI)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │ Input        │───▶│ LLM          │───▶│ MCP          │───▶│ Export     │ │
│  │ Handler      │    │ Service      │    │ Client       │    │ Service    │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └────────────┘ │
│         │                   │                   │                   │        │
│         ▼                   ▼                   ▼                   ▼        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐  ┌────────────┐  │
│  │ File Storage│    │ LangChain   │    │ Canva MCP       │  │ Canva      │  │
│  │ (Local/S3)  │    │ (GPT-4V)    │    │ Server Process  │  │ Export API │  │
│  └─────────────┘    └─────────────┘    └─────────────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Node Specifications

### 1. Input Text Node (`input_text`)

**Purpose:** Collect free-form text input from user.

**Configuration Schema:**
```typescript
interface InputTextNodeConfig {
  placeholder?: string;        // Placeholder text for input field
  maxLength?: number;          // Maximum character limit
  required: boolean;           // Whether input is required
  defaultValue?: string;       // Pre-filled value
}
```

**Output Schema:**
```typescript
interface InputTextOutput {
  text: string;
  charCount: number;
  timestamp: string;
}
```

**UI Components:**
- Multi-line textarea with character counter
- Clear button
- Validation feedback

---

### 2. Input Image Node (`input_image`)

**Purpose:** Accept image input via multiple methods.

**Configuration Schema:**
```typescript
interface InputImageNodeConfig {
  allowUpload: boolean;        // Enable file upload
  allowUrl: boolean;           // Enable URL input
  allowClipboard: boolean;     // Enable paste from clipboard
  maxFileSizeMB: number;       // Max file size (default: 10MB)
  acceptedFormats: string[];   // ['image/png', 'image/jpeg', 'image/webp']
}
```

**Output Schema:**
```typescript
interface InputImageOutput {
  source: 'upload' | 'url' | 'clipboard';
  imageUrl: string;            // Public URL or data URL
  base64?: string;             // Base64 for vision models
  mimeType: string;
  dimensions?: {
    width: number;
    height: number;
  };
}
```

**UI Components:**
- Drag-and-drop upload zone
- URL input field with preview
- Paste detection listener
- Image preview thumbnail
- Remove/replace button

**Backend Handling:**
- File upload endpoint: `POST /api/v1/uploads/image`
- Store temporarily (local filesystem or S3)
- Return accessible URL for downstream processing

---

### 3. Input Combined Node (`input_combined`)

**Purpose:** Accept both text and image in a single node.

**Configuration Schema:**
```typescript
interface InputCombinedNodeConfig {
  textConfig: InputTextNodeConfig;
  imageConfig: InputImageNodeConfig;
  imageRequired: boolean;      // Whether image is mandatory
  textRequired: boolean;       // Whether text is mandatory
}
```

**Output Schema:**
```typescript
interface InputCombinedOutput {
  text: InputTextOutput | null;
  image: InputImageOutput | null;
}
```

---

### 4. LLM Transform Node (`llm_transform`)

**Purpose:** Process input through LLM to transform text and generate Canva instructions.

**Configuration Schema:**
```typescript
interface LLMTransformNodeConfig {
  provider: 'openai' | 'anthropic';
  model: string;

  // Prompt template with variable interpolation
  // Available variables: {{text}}, {{image_description}}, {{user_intent}}
  systemPrompt: string;
  userPromptTemplate: string;

  // Vision settings (for image inputs)
  enableVision: boolean;
  imageDetail: 'low' | 'high' | 'auto';

  // Output structure
  outputFormat: 'text' | 'structured';

  // Canva instruction generation
  generateCanvaInstructions: boolean;
  canvaInstructionPrompt?: string;

  // Advanced
  temperature: number;
  maxTokens: number;
}
```

**Default System Prompt:**
```
You are a design assistant that transforms user input into actionable design instructions for Canva.

Given the user's input (text and/or image), you will:
1. Understand the user's design intent
2. Transform and enhance any text content for the design
3. Generate specific instructions for creating/modifying a Canva design

Output your response in the following JSON structure:
{
  "enhanced_text": "The transformed/enhanced text content",
  "design_intent": "Brief description of what the user wants",
  "canva_instructions": {
    "action": "create" | "modify",
    "design_type": "presentation" | "social_media" | "document" | "poster" | etc,
    "template_query": "search query for template if modifying",
    "elements": [
      {
        "type": "text" | "image" | "shape",
        "content": "...",
        "style": { ... }
      }
    ],
    "style_preferences": {
      "color_scheme": "...",
      "font_style": "...",
      "mood": "..."
    }
  }
}
```

**Output Schema:**
```typescript
interface LLMTransformOutput {
  raw_response: string;
  enhanced_text: string;
  design_intent: string;
  canva_instructions: CanvaInstructions;
  model_used: string;
  tokens_used: {
    prompt: number;
    completion: number;
  };
}

interface CanvaInstructions {
  action: 'create' | 'modify';
  design_type: string;
  template_query?: string;
  elements: CanvaElement[];
  style_preferences: StylePreferences;
}
```

---

### 5. Canva MCP Node (`canva_mcp`)

**Purpose:** Execute Canva operations via MCP protocol.

**Configuration Schema:**
```typescript
interface CanvaMCPNodeConfig {
  // Operation mode
  operation: 'create' | 'modify';

  // Template settings (for modify operation)
  templateSource: 'search' | 'id' | 'from_input';
  templateId?: string;
  templateSearchQuery?: string;

  // Design settings
  designName?: string;
  brandKitId?: string;

  // Output preferences (selected upfront)
  outputFormat: 'pdf' | 'png' | 'jpg' | 'link';
  exportQuality?: 'standard' | 'high';

  // Advanced
  timeout: number;             // MCP call timeout in ms
}
```

**MCP Tool Calls:**

Based on Canva MCP capabilities, the node will invoke:

```typescript
// Tool: canva_create_design
{
  tool: "canva_create_design",
  arguments: {
    design_type: string,
    title: string,
    elements: CanvaElement[],
  }
}

// Tool: canva_search_templates
{
  tool: "canva_search_templates",
  arguments: {
    query: string,
    design_type?: string,
    limit?: number,
  }
}

// Tool: canva_modify_design
{
  tool: "canva_modify_design",
  arguments: {
    design_id: string,
    modifications: Modification[],
  }
}

// Tool: canva_export_design
{
  tool: "canva_export_design",
  arguments: {
    design_id: string,
    format: 'pdf' | 'png' | 'jpg',
    quality?: 'standard' | 'high',
  }
}
```

**Output Schema:**
```typescript
interface CanvaMCPOutput {
  success: boolean;
  design_id: string;
  design_url: string;          // Editable Canva URL
  export_url?: string;         // If export was requested
  export_format?: string;
  thumbnail_url?: string;
  error?: string;
}
```

---

### 6. Output Export Node (`output_export`)

**Purpose:** Handle final output delivery based on user's upfront selection.

**Configuration Schema:**
```typescript
interface OutputExportNodeConfig {
  outputType: 'pdf' | 'image' | 'link';

  // PDF options
  pdfOptions?: {
    pageSize: 'A4' | 'Letter' | 'Original';
    quality: 'standard' | 'print';
  };

  // Image options
  imageOptions?: {
    format: 'png' | 'jpg' | 'webp';
    quality: number;           // 1-100
    scale: number;             // 1x, 2x, etc.
  };

  // Link options
  linkOptions?: {
    accessLevel: 'view' | 'edit';
    expiresIn?: number;        // Hours until expiry
  };

  // Delivery
  downloadAutomatically: boolean;
  showPreview: boolean;
}
```

**Output Schema:**
```typescript
interface OutputExportResult {
  outputType: 'pdf' | 'image' | 'link';
  url: string;
  filename?: string;
  fileSize?: number;
  previewUrl?: string;
  canvaEditUrl: string;        // Always provide editable link
  expiresAt?: string;
}
```

---

## Backend Implementation

### File Structure Additions

```
backend/app/
├── api/v1/endpoints/
│   ├── uploads.py             # NEW: File upload handling
│   └── exports.py             # NEW: Export management
├── core/
│   └── mcp.py                 # NEW: MCP client setup using langchain-mcp-adapters
├── models/
│   └── upload.py              # NEW: Upload tracking model
├── schemas/
│   ├── input.py               # NEW: Input node schemas
│   ├── canva.py               # NEW: Canva operation schemas
│   └── export.py              # NEW: Export schemas
├── services/
│   ├── input_service.py       # NEW: Input processing
│   ├── canva_service.py       # NEW: Canva operations (high-level wrapper)
│   └── export_service.py      # NEW: Export handling
└── utils/
    └── image_utils.py         # NEW: Image processing utilities
```

### Dependencies

Add to `pyproject.toml`:
```toml
[project.dependencies]
langchain-mcp-adapters = ">=0.2.1"
```

### API Endpoints

#### Upload Endpoints

```python
# POST /api/v1/uploads/image
# Upload image file and return accessible URL
@router.post("/image", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    session_id: str = Query(...),
) -> ImageUploadResponse:
    """
    Upload an image file for use in the pipeline.
    Returns a temporary URL valid for 24 hours.
    """
    pass

# POST /api/v1/uploads/image-url
# Fetch image from URL and store locally
@router.post("/image-url", response_model=ImageUploadResponse)
async def upload_image_from_url(
    request: ImageUrlRequest,
) -> ImageUploadResponse:
    """
    Fetch an image from a URL and store it locally.
    Validates the URL and checks file size/type.
    """
    pass
```

#### Canva MCP Endpoints

```python
# POST /api/v1/canva/create
# Create a new Canva design
@router.post("/create", response_model=CanvaDesignResponse)
async def create_design(
    request: CreateDesignRequest,
) -> CanvaDesignResponse:
    """
    Create a new Canva design using MCP.
    """
    pass

# POST /api/v1/canva/modify
# Modify existing template/design
@router.post("/modify", response_model=CanvaDesignResponse)
async def modify_design(
    request: ModifyDesignRequest,
) -> CanvaDesignResponse:
    """
    Modify an existing Canva design or template.
    """
    pass

# GET /api/v1/canva/templates
# Search for templates
@router.get("/templates", response_model=TemplateSearchResponse)
async def search_templates(
    query: str = Query(...),
    design_type: Optional[str] = Query(None),
    limit: int = Query(10, le=50),
) -> TemplateSearchResponse:
    """
    Search Canva templates by query.
    """
    pass

# POST /api/v1/canva/export/{design_id}
# Export design to specified format
@router.post("/export/{design_id}", response_model=ExportResponse)
async def export_design(
    design_id: str,
    request: ExportRequest,
) -> ExportResponse:
    """
    Export a Canva design to PDF, PNG, or JPG.
    """
    pass
```

### MCP Client Setup (using langchain-mcp-adapters)

The `langchain-mcp-adapters` library provides a clean abstraction for connecting to MCP servers and converting their tools to LangChain-compatible tools. This eliminates the need for custom MCP protocol handling.

```python
# backend/app/core/mcp.py

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool
from app.core.config import settings

# MCP Server Configuration
MCP_SERVERS_CONFIG = {
    "canva": {
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@canva/cli@latest", "mcp"],
    },
    # Future MCP servers can be added here
    # "filesystem": {
    #     "transport": "stdio",
    #     "command": "npx",
    #     "args": ["-y", "@anthropic-ai/mcp-filesystem"],
    # },
}


class MCPClientManager:
    """
    Manages MCP client connections using langchain-mcp-adapters.
    Provides tools that can be used directly with LangGraph agents.
    """

    def __init__(self):
        self._client: MultiServerMCPClient | None = None
        self._tools: list[BaseTool] = []

    async def initialize(self) -> None:
        """Initialize the MCP client and load tools from all servers."""
        self._client = MultiServerMCPClient(MCP_SERVERS_CONFIG)
        self._tools = await self._client.get_tools()

    async def get_tools(self) -> list[BaseTool]:
        """Get all loaded MCP tools as LangChain tools."""
        if not self._tools:
            await self.initialize()
        return self._tools

    async def get_canva_tools(self) -> list[BaseTool]:
        """Get only Canva-related tools."""
        all_tools = await self.get_tools()
        # Filter tools by name prefix if needed
        return [t for t in all_tools if "canva" in t.name.lower()]

    async def shutdown(self) -> None:
        """Cleanup MCP client connections."""
        if self._client:
            # MultiServerMCPClient handles cleanup automatically
            self._client = None
            self._tools = []


# Global singleton instance
mcp_manager = MCPClientManager()


# Dependency injection helper for FastAPI
async def get_mcp_tools() -> list[BaseTool]:
    """FastAPI dependency for getting MCP tools."""
    return await mcp_manager.get_tools()
```

### MCP Tool Interceptors (Optional Advanced Usage)

Interceptors provide middleware-like control over MCP tool execution:

```python
# backend/app/core/mcp_interceptors.py

import asyncio
from typing import Any

async def retry_interceptor(
    request: Any,
    handler: Any,
    max_retries: int = 3,
) -> Any:
    """Retry failed MCP tool calls with exponential backoff."""
    last_error = None

    for attempt in range(max_retries):
        try:
            return await handler(request)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(1.0 * (2 ** attempt))

    raise last_error


async def logging_interceptor(request: Any, handler: Any) -> Any:
    """Log MCP tool calls for debugging."""
    import logging
    logger = logging.getLogger("mcp")

    logger.info(f"MCP Tool Call: {request.tool_name}")
    logger.debug(f"Arguments: {request.args}")

    result = await handler(request)

    logger.info(f"MCP Tool Result: success")
    return result


async def inject_context_interceptor(request: Any, handler: Any) -> Any:
    """Inject runtime context into MCP tool calls."""
    # Access LangGraph runtime context if available
    runtime = getattr(request, 'runtime', None)
    if runtime and hasattr(runtime, 'context'):
        # Modify request args with context data
        modified_args = {**request.args}
        if hasattr(runtime.context, 'user_id'):
            modified_args['user_context'] = {
                'user_id': runtime.context.user_id,
            }
        request = request.override(args=modified_args)

    return await handler(request)


# Configure interceptors when creating client
def get_mcp_client_with_interceptors() -> MultiServerMCPClient:
    """Create MCP client with interceptors enabled."""
    from langchain_mcp_adapters.client import MultiServerMCPClient

    return MultiServerMCPClient(
        MCP_SERVERS_CONFIG,
        tool_interceptors=[
            logging_interceptor,
            retry_interceptor,
        ]
    )
```

### Canva Service (High-Level Wrapper)

```python
# backend/app/services/canva_service.py

from langchain_core.tools import BaseTool
from app.core.mcp import mcp_manager
from app.schemas.canva import CanvaDesignResponse, CanvaInstructions


class CanvaService:
    """
    High-level service for Canva operations.
    Wraps MCP tools with business logic.
    """

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    async def _ensure_tools(self) -> None:
        """Ensure Canva tools are loaded."""
        if not self._tools:
            tools = await mcp_manager.get_canva_tools()
            self._tools = {t.name: t for t in tools}

    async def create_design(
        self,
        design_type: str,
        title: str,
        elements: list[dict],
        style: dict | None = None,
    ) -> CanvaDesignResponse:
        """Create a new Canva design."""
        await self._ensure_tools()

        # Find the create design tool
        create_tool = self._tools.get("canva_create_design")
        if not create_tool:
            raise ValueError("Canva create_design tool not available")

        result = await create_tool.ainvoke({
            "design_type": design_type,
            "title": title,
            "elements": elements,
            "style": style,
        })

        return CanvaDesignResponse.model_validate(result)

    async def search_templates(
        self,
        query: str,
        design_type: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Search for Canva templates."""
        await self._ensure_tools()

        search_tool = self._tools.get("canva_search_templates")
        if not search_tool:
            raise ValueError("Canva search_templates tool not available")

        result = await search_tool.ainvoke({
            "query": query,
            "design_type": design_type,
            "limit": limit,
        })

        return result.get("templates", [])

    async def modify_design(
        self,
        design_id: str,
        modifications: list[dict],
    ) -> CanvaDesignResponse:
        """Modify an existing design."""
        await self._ensure_tools()

        modify_tool = self._tools.get("canva_modify_design")
        if not modify_tool:
            raise ValueError("Canva modify_design tool not available")

        result = await modify_tool.ainvoke({
            "design_id": design_id,
            "modifications": modifications,
        })

        return CanvaDesignResponse.model_validate(result)

    async def export_design(
        self,
        design_id: str,
        format: str,
        quality: str = "standard",
    ) -> dict:
        """Export design to specified format."""
        await self._ensure_tools()

        export_tool = self._tools.get("canva_export_design")
        if not export_tool:
            raise ValueError("Canva export_design tool not available")

        return await export_tool.ainvoke({
            "design_id": design_id,
            "format": format,
            "quality": quality,
        })


# Global service instance
canva_service = CanvaService()
```

### LangGraph Node Factories

```python
# backend/app/services/graph_service.py (additions)

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

async def create_input_text_node(config: dict) -> Callable:
    """Factory for input text node."""
    async def input_text_node(state: GraphState) -> dict:
        # Input is provided at execution time
        user_input = state.get("user_input", {})
        text = user_input.get("text", "")

        return {
            "input_text": text,
            "input_type": "text",
        }
    return input_text_node

async def create_input_image_node(config: dict) -> Callable:
    """Factory for input image node."""
    async def input_image_node(state: GraphState) -> dict:
        user_input = state.get("user_input", {})
        image_data = user_input.get("image", {})

        return {
            "input_image_url": image_data.get("url"),
            "input_image_base64": image_data.get("base64"),
            "input_type": "image",
        }
    return input_image_node

async def create_llm_transform_node(config: dict) -> Callable:
    """Factory for LLM transform node with vision support."""

    provider = config.get("provider", "openai")
    model = config.get("model", "gpt-4o")
    system_prompt = config.get("systemPrompt", DEFAULT_TRANSFORM_PROMPT)
    user_template = config.get("userPromptTemplate", "{{text}}")
    enable_vision = config.get("enableVision", True)

    llm = get_llm(provider, model)

    async def llm_transform_node(state: GraphState) -> dict:
        messages = [{"role": "system", "content": system_prompt}]

        # Build user message with text and/or image
        content = []

        if state.get("input_text"):
            text_content = user_template.replace("{{text}}", state["input_text"])
            content.append({"type": "text", "text": text_content})

        if enable_vision and state.get("input_image_url"):
            content.append({
                "type": "image_url",
                "image_url": {"url": state["input_image_url"]}
            })

        messages.append({"role": "user", "content": content})

        response = await llm.ainvoke(messages)

        # Parse structured output
        parsed = parse_llm_response(response.content)

        return {
            "enhanced_text": parsed.get("enhanced_text", ""),
            "design_intent": parsed.get("design_intent", ""),
            "canva_instructions": parsed.get("canva_instructions", {}),
            "messages": [response],
        }

    return llm_transform_node

async def create_canva_mcp_node(config: dict) -> Callable:
    """Factory for Canva MCP node using langchain-mcp-adapters."""

    from app.services.canva_service import canva_service

    operation = config.get("operation", "create")
    output_format = config.get("outputFormat", "link")

    async def canva_mcp_node(state: GraphState) -> dict:
        instructions = state.get("canva_instructions", {})

        if operation == "create":
            result = await canva_service.create_design(
                design_type=instructions.get("design_type", "document"),
                title=state.get("design_intent", "Untitled"),
                elements=instructions.get("elements", []),
                style=instructions.get("style_preferences"),
            )
        else:  # modify
            template_id = await resolve_template(canva_service, config, instructions)
            result = await canva_service.modify_design(
                design_id=template_id,
                modifications=instructions.get("elements", []),
            )

        # Export if needed
        export_result = None
        if output_format != "link":
            export_result = await canva_service.export_design(
                design_id=result.design_id,
                format=output_format,
            )

        return {
            "canva_design_id": result.design_id,
            "canva_design_url": result.design_url,
            "canva_export_url": export_result.get("url") if export_result else None,
            "canva_export_format": output_format,
        }

    return canva_mcp_node


async def resolve_template(
    canva_service: "CanvaService",
    config: dict,
    instructions: dict,
) -> str:
    """Resolve template ID from config or search."""
    template_source = config.get("templateSource", "from_input")

    if template_source == "id":
        return config.get("templateId")
    elif template_source == "search":
        query = config.get("templateSearchQuery") or instructions.get("template_query", "")
        templates = await canva_service.search_templates(
            query=query,
            design_type=instructions.get("design_type"),
            limit=1,
        )
        if templates:
            return templates[0]["id"]
        raise ValueError(f"No template found for query: {query}")
    else:  # from_input
        query = instructions.get("template_query", "")
        if not query:
            raise ValueError("No template query provided in LLM instructions")
        templates = await canva_service.search_templates(
            query=query,
            design_type=instructions.get("design_type"),
            limit=1,
        )
        if templates:
            return templates[0]["id"]
        raise ValueError(f"No template found for query: {query}")

async def create_output_export_node(config: dict) -> Callable:
    """Factory for output export node."""

    output_type = config.get("outputType", "link")

    async def output_export_node(state: GraphState) -> dict:
        return {
            "final_output": {
                "type": output_type,
                "url": state.get("canva_export_url") or state.get("canva_design_url"),
                "edit_url": state.get("canva_design_url"),
                "design_id": state.get("canva_design_id"),
            }
        }

    return output_export_node
```

---

## Frontend Implementation

### File Structure Additions

```
frontend/src/
├── components/
│   └── graph/
│       ├── nodes/
│       │   ├── InputTextNode.tsx      # NEW
│       │   ├── InputImageNode.tsx     # NEW
│       │   ├── InputCombinedNode.tsx  # NEW
│       │   ├── LLMTransformNode.tsx   # NEW
│       │   ├── CanvaMCPNode.tsx       # NEW
│       │   └── OutputExportNode.tsx   # NEW
│       ├── config/
│       │   ├── InputTextConfig.tsx    # NEW
│       │   ├── InputImageConfig.tsx   # NEW
│       │   ├── LLMTransformConfig.tsx # NEW
│       │   ├── CanvaMCPConfig.tsx     # NEW
│       │   └── OutputExportConfig.tsx # NEW
│       └── shared/
│           ├── ImageUploader.tsx      # NEW
│           └── PromptEditor.tsx       # NEW
├── hooks/
│   ├── useImageUpload.ts              # NEW
│   └── useCanvaExport.ts              # NEW
├── services/
│   ├── uploadService.ts               # NEW
│   └── canvaService.ts                # NEW
└── types/
    ├── input.ts                       # NEW
    ├── canva.ts                       # NEW
    └── export.ts                      # NEW
```

### Type Definitions

```typescript
// frontend/src/types/input.ts

export type InputSource = 'upload' | 'url' | 'clipboard';

export interface TextInput {
  text: string;
  charCount: number;
}

export interface ImageInput {
  source: InputSource;
  url: string;
  base64?: string;
  mimeType: string;
  dimensions?: {
    width: number;
    height: number;
  };
  file?: File;
}

export interface CombinedInput {
  text?: TextInput;
  image?: ImageInput;
}
```

```typescript
// frontend/src/types/canva.ts

export type CanvaOperation = 'create' | 'modify';
export type CanvaOutputFormat = 'pdf' | 'png' | 'jpg' | 'link';

export interface CanvaDesignType {
  id: string;
  name: string;
  icon: string;
}

export const CANVA_DESIGN_TYPES: CanvaDesignType[] = [
  { id: 'presentation', name: 'Presentation', icon: 'slides' },
  { id: 'social_media', name: 'Social Media', icon: 'share' },
  { id: 'document', name: 'Document', icon: 'file' },
  { id: 'poster', name: 'Poster', icon: 'image' },
  { id: 'video', name: 'Video', icon: 'video' },
  { id: 'whiteboard', name: 'Whiteboard', icon: 'board' },
];

export interface CanvaTemplate {
  id: string;
  title: string;
  thumbnailUrl: string;
  designType: string;
}

export interface CanvaDesignResult {
  designId: string;
  designUrl: string;
  exportUrl?: string;
  thumbnailUrl?: string;
}
```

### Input Image Node Component

```tsx
// frontend/src/components/graph/nodes/InputImageNode.tsx

import { memo, useState, useCallback } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { useDropzone } from 'react-dropzone';
import { ImageInput, InputSource } from '@/types/input';
import { uploadImage, fetchImageFromUrl } from '@/services/uploadService';

interface InputImageNodeData {
  label: string;
  nodeType: 'input_image';
  config: {
    allowUpload: boolean;
    allowUrl: boolean;
    allowClipboard: boolean;
    maxFileSizeMB: number;
  };
  value?: ImageInput;
}

export const InputImageNode = memo(({ data, id }: NodeProps<InputImageNodeData>) => {
  const [imageData, setImageData] = useState<ImageInput | null>(data.value || null);
  const [urlInput, setUrlInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setLoading(true);
    setError(null);

    try {
      const result = await uploadImage(file);
      setImageData({
        source: 'upload',
        url: result.url,
        mimeType: file.type,
        dimensions: result.dimensions,
        file,
      });
    } catch (err) {
      setError('Failed to upload image');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleUrlSubmit = useCallback(async () => {
    if (!urlInput.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const result = await fetchImageFromUrl(urlInput);
      setImageData({
        source: 'url',
        url: result.url,
        mimeType: result.mimeType,
        dimensions: result.dimensions,
      });
    } catch (err) {
      setError('Failed to fetch image from URL');
    } finally {
      setLoading(false);
    }
  }, [urlInput]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleFileDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp'],
    },
    maxSize: (data.config.maxFileSizeMB || 10) * 1024 * 1024,
    disabled: !data.config.allowUpload,
  });

  return (
    <div className="bg-white rounded-lg shadow-md border-2 border-purple-400 min-w-[280px]">
      <div className="bg-purple-400 text-white px-3 py-2 rounded-t-md font-medium">
        {data.label || 'Image Input'}
      </div>

      <div className="p-3 space-y-3">
        {/* Upload Zone */}
        {data.config.allowUpload && (
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-md p-4 text-center cursor-pointer
              transition-colors
              ${isDragActive ? 'border-purple-500 bg-purple-50' : 'border-gray-300'}
              ${loading ? 'opacity-50 pointer-events-none' : ''}
            `}
          >
            <input {...getInputProps()} />
            {imageData ? (
              <img
                src={imageData.url}
                alt="Preview"
                className="max-h-32 mx-auto rounded"
              />
            ) : (
              <p className="text-gray-500 text-sm">
                {isDragActive ? 'Drop image here' : 'Drag & drop or click to upload'}
              </p>
            )}
          </div>
        )}

        {/* URL Input */}
        {data.config.allowUrl && (
          <div className="flex gap-2">
            <input
              type="url"
              placeholder="Paste image URL..."
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              className="flex-1 px-2 py-1 border rounded text-sm"
            />
            <button
              onClick={handleUrlSubmit}
              disabled={loading}
              className="px-3 py-1 bg-purple-500 text-white rounded text-sm hover:bg-purple-600"
            >
              Fetch
            </button>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <p className="text-red-500 text-xs">{error}</p>
        )}

        {/* Image Info */}
        {imageData && (
          <div className="text-xs text-gray-500 flex justify-between">
            <span>Source: {imageData.source}</span>
            {imageData.dimensions && (
              <span>{imageData.dimensions.width}x{imageData.dimensions.height}</span>
            )}
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
});
```

### Canva MCP Node Component

```tsx
// frontend/src/components/graph/nodes/CanvaMCPNode.tsx

import { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { CanvaOperation, CanvaOutputFormat, CANVA_DESIGN_TYPES } from '@/types/canva';

interface CanvaMCPNodeData {
  label: string;
  nodeType: 'canva_mcp';
  config: {
    operation: CanvaOperation;
    templateSource: 'search' | 'id' | 'from_input';
    templateId?: string;
    templateSearchQuery?: string;
    designType?: string;
    outputFormat: CanvaOutputFormat;
  };
}

export const CanvaMCPNode = memo(({ data, id }: NodeProps<CanvaMCPNodeData>) => {
  const { config } = data;

  return (
    <div className="bg-white rounded-lg shadow-md border-2 border-pink-400 min-w-[280px]">
      <Handle type="target" position={Position.Top} />

      <div className="bg-pink-400 text-white px-3 py-2 rounded-t-md font-medium flex items-center gap-2">
        <CanvaIcon className="w-4 h-4" />
        {data.label || 'Canva MCP'}
      </div>

      <div className="p-3 space-y-2 text-sm">
        {/* Operation Badge */}
        <div className="flex gap-2">
          <span className={`
            px-2 py-0.5 rounded text-xs font-medium
            ${config.operation === 'create' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}
          `}>
            {config.operation === 'create' ? 'Create New' : 'Modify Template'}
          </span>
        </div>

        {/* Design Type */}
        {config.designType && (
          <div className="flex items-center gap-2 text-gray-600">
            <span>Type:</span>
            <span className="font-medium">
              {CANVA_DESIGN_TYPES.find(t => t.id === config.designType)?.name}
            </span>
          </div>
        )}

        {/* Template Info */}
        {config.operation === 'modify' && (
          <div className="text-gray-600">
            Template: {config.templateSource === 'search'
              ? `Search: "${config.templateSearchQuery}"`
              : config.templateSource === 'id'
                ? `ID: ${config.templateId}`
                : 'From LLM instructions'
            }
          </div>
        )}

        {/* Output Format */}
        <div className="flex items-center gap-2 pt-2 border-t">
          <span className="text-gray-500">Output:</span>
          <span className={`
            px-2 py-0.5 rounded text-xs font-medium uppercase
            ${config.outputFormat === 'link' ? 'bg-purple-100 text-purple-700' : 'bg-orange-100 text-orange-700'}
          `}>
            {config.outputFormat}
          </span>
        </div>
      </div>

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
});

const CanvaIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
  </svg>
);
```

---

## MCP Server Setup

### Environment Configuration

```bash
# .env additions

# Canva MCP Configuration
CANVA_MCP_ENABLED=true
CANVA_MCP_TIMEOUT=30000

# File Upload Configuration
UPLOAD_DIR=./uploads
UPLOAD_MAX_SIZE_MB=10
UPLOAD_ALLOWED_TYPES=image/png,image/jpeg,image/webp
UPLOAD_URL_BASE=http://localhost:8000/uploads
```

### Prerequisites

Ensure Node.js v20+ and npm are installed for running MCP servers via npx:

```bash
# Verify Node.js version
node --version  # Should be v20+

# The Canva MCP server will be automatically downloaded via npx
# No manual installation required
```

### FastAPI Lifespan Integration

```python
# backend/app/main.py (updated lifespan)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.mcp import mcp_manager
from app.db.database import init_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_db()

    # Initialize MCP clients (optional: can be lazy-loaded)
    # await mcp_manager.initialize()

    yield

    # Shutdown
    await mcp_manager.shutdown()
    await close_db()

app = FastAPI(lifespan=lifespan)
```

### Alternative: LangGraph Agent with MCP Tools

For more sophisticated workflows, you can create a LangGraph agent that has access to all MCP tools:

```python
# backend/app/services/agent_service.py

from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from app.core.mcp import mcp_manager


async def create_canva_agent():
    """Create a LangGraph agent with Canva MCP tools."""

    # Get MCP tools
    tools = await mcp_manager.get_canva_tools()

    # Create LLM with tools bound
    llm = ChatOpenAI(model="gpt-4o").bind_tools(tools)

    async def call_model(state: MessagesState):
        response = await llm.ainvoke(state["messages"])
        return {"messages": [response]}

    # Build the graph
    builder = StateGraph(MessagesState)
    builder.add_node("agent", call_model)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge("__start__", "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")

    return builder.compile()


# Usage:
# agent = await create_canva_agent()
# result = await agent.ainvoke({
#     "messages": [HumanMessage(content="Create a presentation about AI")]
# })
```

---

## Execution Flow

### Complete Pipeline Execution

```python
# backend/app/services/workflow_service.py (additions)

async def execute_canva_pipeline(
    workflow_id: str,
    user_input: dict,
    thread_id: str | None = None,
) -> dict:
    """
    Execute a complete input-to-Canva pipeline.

    Flow:
    1. Process user input (text/image)
    2. Run through LLM transform
    3. Execute Canva MCP operations
    4. Export and return result
    """

    # Load workflow and graph
    workflow = await Workflow.get(workflow_id)
    graph = await Graph.get(workflow.graph_id)

    # Build LangGraph from configuration
    executor = GraphExecutor(graph.config)
    compiled_graph = await executor.compile()

    # Prepare initial state
    initial_state = {
        "user_input": user_input,
        "messages": [],
    }

    # Execute with checkpointing
    config = {
        "configurable": {"thread_id": thread_id or str(uuid4())}
    }

    result = await compiled_graph.ainvoke(initial_state, config)

    return {
        "thread_id": config["configurable"]["thread_id"],
        "output": result.get("final_output"),
        "design_url": result.get("canva_design_url"),
        "export_url": result.get("canva_export_url"),
    }
```

### Frontend Execution Handler

```typescript
// frontend/src/hooks/useWorkflowExecution.ts

import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { executeWorkflow, ExecutionInput, ExecutionResult } from '@/services/api';

export function useWorkflowExecution(workflowId: string) {
  const [executionState, setExecutionState] = useState<'idle' | 'running' | 'completed' | 'error'>('idle');

  const mutation = useMutation({
    mutationFn: (input: ExecutionInput) => executeWorkflow(workflowId, input),
    onMutate: () => setExecutionState('running'),
    onSuccess: () => setExecutionState('completed'),
    onError: () => setExecutionState('error'),
  });

  const execute = useCallback(async (input: ExecutionInput) => {
    return mutation.mutateAsync(input);
  }, [mutation]);

  return {
    execute,
    executionState,
    result: mutation.data,
    error: mutation.error,
    isLoading: mutation.isPending,
  };
}
```

---

## Implementation Phases

### Phase 1.1: Input Nodes (Week 1)

**Tasks:**
1. Create `InputTextNode` component with textarea
2. Create `InputImageNode` component with upload/URL/paste
3. Create `InputCombinedNode` component
4. Implement file upload backend endpoint
5. Add image URL fetching endpoint
6. Add clipboard paste handling
7. Update node type definitions
8. Add input nodes to NodePalette

**Deliverables:**
- Working input nodes in graph editor
- File upload functional
- URL fetching functional
- Clipboard paste working

### Phase 1.2: LLM Transform Node (Week 2)

**Tasks:**
1. Extend existing LLM node for vision capabilities
2. Create `LLMTransformConfig` component
3. Implement prompt template editor
4. Add structured output parsing
5. Create default Canva instruction prompts
6. Test with GPT-4V and Claude vision models

**Deliverables:**
- LLM transform node with vision
- Customizable prompts
- Structured Canva instruction output

### Phase 1.3: Canva MCP Integration (Week 3)

**Tasks:**
1. Install and configure `langchain-mcp-adapters`
2. Create `MCPClientManager` in `app/core/mcp.py`
3. Create `CanvaService` wrapper in `app/services/canva_service.py`
4. Implement design creation flow using MCP tools
5. Implement template search/modify flow
6. Create `CanvaMCPNode` component (frontend)
7. Create `CanvaMCPConfig` component (frontend)
8. Add interceptors for logging and retries
9. Test MCP tool discovery and invocation

**Deliverables:**
- Working MCP integration via `langchain-mcp-adapters`
- Canva tools automatically loaded as LangChain tools
- Create/modify design operations
- Template search functionality
- Error handling with retry logic

### Phase 1.4: Output Export Node (Week 4)

**Tasks:**
1. Implement export service
2. Create `OutputExportNode` component
3. Create `OutputExportConfig` component
4. Add PDF export functionality
5. Add image export functionality
6. Implement link generation with access control
7. Add download handling

**Deliverables:**
- Export to PDF/PNG/JPG
- Editable Canva links
- Automatic download option

### Phase 1.5: Integration & Testing (Week 5)

**Tasks:**
1. End-to-end pipeline testing
2. Error handling across nodes
3. Loading states and progress indication
4. Edge case handling
5. Performance optimization
6. Documentation

**Deliverables:**
- Complete working pipeline
- Error handling
- User feedback during execution
- Documentation

---

## Testing Strategy

### Unit Tests

```python
# backend/tests/test_canva_service.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.canva_service import CanvaService


@pytest.fixture
def mock_mcp_manager():
    """Mock the MCP manager for testing."""
    with patch('app.services.canva_service.mcp_manager') as mock:
        # Create mock tools
        mock_create_tool = MagicMock()
        mock_create_tool.name = "canva_create_design"
        mock_create_tool.ainvoke = AsyncMock(return_value={
            'design_id': 'test-123',
            'design_url': 'https://canva.com/design/test-123',
        })

        mock_export_tool = MagicMock()
        mock_export_tool.name = "canva_export_design"
        mock_export_tool.ainvoke = AsyncMock(return_value={
            'url': 'https://canva.com/export/test-123.pdf',
        })

        mock.get_canva_tools = AsyncMock(return_value=[
            mock_create_tool,
            mock_export_tool,
        ])

        yield mock


@pytest.mark.asyncio
async def test_create_design(mock_mcp_manager):
    """Test design creation via MCP tools."""
    service = CanvaService()

    result = await service.create_design(
        design_type='presentation',
        title='Test Design',
        elements=[],
    )

    assert result.design_id == 'test-123'
    assert 'canva.com' in result.design_url


@pytest.mark.asyncio
async def test_export_design(mock_mcp_manager):
    """Test design export via MCP tools."""
    service = CanvaService()

    result = await service.export_design(
        design_id='test-123',
        format='pdf',
    )

    assert 'url' in result
    assert 'pdf' in result['url']


@pytest.mark.asyncio
async def test_tool_not_available():
    """Test error handling when tool is not available."""
    with patch('app.services.canva_service.mcp_manager') as mock:
        mock.get_canva_tools = AsyncMock(return_value=[])

        service = CanvaService()

        with pytest.raises(ValueError, match="not available"):
            await service.create_design(
                design_type='presentation',
                title='Test',
                elements=[],
            )
```

```typescript
// frontend/src/components/graph/nodes/__tests__/InputImageNode.test.tsx

import { render, screen, fireEvent } from '@testing-library/react';
import { InputImageNode } from '../InputImageNode';

describe('InputImageNode', () => {
  it('renders upload zone when allowUpload is true', () => {
    render(
      <InputImageNode
        data={{
          label: 'Test',
          nodeType: 'input_image',
          config: { allowUpload: true, allowUrl: false, allowClipboard: false, maxFileSizeMB: 10 },
        }}
        id="test-1"
      />
    );

    expect(screen.getByText(/drag & drop/i)).toBeInTheDocument();
  });

  it('handles file drop correctly', async () => {
    // Test file drop
  });
});
```

### Integration Tests

```python
# backend/tests/integration/test_canva_pipeline.py

import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_complete_pipeline():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create workflow with all nodes
        workflow_response = await client.post("/api/v1/workflows", json={
            "name": "Test Canva Pipeline",
            "graph_config": {
                "nodes": [...],
                "edges": [...],
            }
        })
        workflow_id = workflow_response.json()["id"]

        # Execute with test input
        result = await client.post(f"/api/v1/workflows/{workflow_id}/execute", json={
            "user_input": {
                "text": "Create a presentation about AI",
            }
        })

        assert result.status_code == 200
        assert "design_url" in result.json()
```

---

## Error Handling

### Error Types

```typescript
// frontend/src/types/errors.ts

export enum PipelineErrorCode {
  INPUT_VALIDATION = 'INPUT_VALIDATION',
  UPLOAD_FAILED = 'UPLOAD_FAILED',
  LLM_ERROR = 'LLM_ERROR',
  MCP_CONNECTION = 'MCP_CONNECTION',
  CANVA_API = 'CANVA_API',
  EXPORT_FAILED = 'EXPORT_FAILED',
  TIMEOUT = 'TIMEOUT',
}

export interface PipelineError {
  code: PipelineErrorCode;
  message: string;
  nodeId?: string;
  details?: Record<string, unknown>;
  recoverable: boolean;
}
```

### Error Recovery

```python
# backend/app/services/error_handler.py

from enum import Enum
from typing import Callable, TypeVar

class RetryStrategy(Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    NONE = "none"

T = TypeVar('T')

async def with_retry(
    fn: Callable[[], T],
    max_retries: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    recoverable_errors: tuple = (ConnectionError, TimeoutError),
) -> T:
    """Execute function with retry logic."""
    last_error = None

    for attempt in range(max_retries):
        try:
            return await fn()
        except recoverable_errors as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = calculate_delay(attempt, strategy)
                await asyncio.sleep(delay)

    raise last_error
```

---

## Security Considerations

1. **File Upload Security**
   - Validate file types on both client and server
   - Scan uploaded files for malware
   - Limit file sizes
   - Store files in isolated location

2. **API Key Management**
   - Store Canva API keys in environment variables
   - Never expose keys to frontend
   - Rotate keys regularly

3. **MCP Security**
   - Run MCP servers in sandboxed environment
   - Validate all tool call arguments
   - Implement rate limiting

4. **User Data**
   - Clear temporary uploads after pipeline completion
   - Don't persist sensitive user input
   - Implement proper access control for designs

---

## Open Questions / Assumptions

1. **Canva MCP Server Availability**: This plan assumes the Canva MCP server (`@canva/cli@latest mcp`) provides the tools described. The actual tool names and parameters may differ - run `await mcp_manager.get_canva_tools()` to discover available tools.

2. **Authentication Flow**: The plan assumes Canva API authentication is handled at the backend level via environment variables or the MCP server's built-in auth. OAuth flow for user-specific Canva accounts is not covered in Phase 1.

3. **Rate Limits**: Canva API rate limits are not addressed. May need queueing system for high-volume usage.

4. **Real-time Updates**: Current plan uses request-response pattern. WebSocket updates for long-running operations could be added.

5. **Branching Implementation**: The branching feature (multiple outputs from single LLM) is architecturally supported but UI for managing branches needs design.

6. **MCP Protocol Version**: The `langchain-mcp-adapters` library supports MCP Protocol version 2025-03-26 and maintains backwards compatibility with 2024-11-05. Ensure the Canva MCP server is compatible.

---

## Key Library Reference

### langchain-mcp-adapters

- **Version**: 0.2.1+
- **PyPI**: https://pypi.org/project/langchain-mcp-adapters/
- **GitHub**: https://github.com/langchain-ai/langchain-mcp-adapters
- **Docs**: https://docs.langchain.com/oss/python/langchain/mcp

**Key Features:**
- `MultiServerMCPClient`: Connect to multiple MCP servers simultaneously
- Automatic tool conversion to LangChain-compatible tools
- Support for stdio, HTTP, SSE, and streamable HTTP transports
- Tool interceptors for middleware-like control
- Built-in support for resources and prompts from MCP servers
