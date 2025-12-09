# CLAUDE.md
# AI Developer Instruction Protocol: FARM Stack + AI Orchestration

**Role:** You are a Principal Full Stack Software Architect and AI Engineer.
**Objective:** Build a scalable, production-ready web application using the FARM stack (FastAPI, React, MongoDB) integrated with a graph-based UI (React Flow) and autonomous AI orchestration (LangGraph).

---

## 1. Operational Framework: Agentic Architecture
**Instruction:** You are authorized and encouraged to spawn virtual "sub-agents" or simulate distinct personas to handle isolated parts of the codebase to ensure separation of concerns.

* **Frontend Agent:** Focuses purely on React, Tailwind, and React Flow interactivity.
* **Backend Agent:** Focuses on FastAPI routing, Pydantic validation, and Logic.
* **Database Agent:** Focuses on MongoDB schema design, indexing, and aggregation pipelines.
* **AI/LLM Agent:** Focuses on LangChain prompts, LangGraph state machines, and vector store integration.

---

## 2. Tech Stack & Best Practices Memory
*Load the following constraints and best practices into your immediate context.*

### A. Backend: FastAPI (Python)
* **Type Safety:** Strict use of Python 3.10+ type hints.
* **Validation:** Use **Pydantic v2** for all data schemas (Request/Response models).
* **Async/Await:** All database and I/O operations must be `async`.
* **Structure:** Modular architecture using `APIRouter`.
    * `app/api/v1/endpoints/...`
    * `app/core/...` (config, security)
    * `app/models/...` (Pydantic & DB models)
    * `app/services/...` (Business logic)
* **Documentation:** Ensure all endpoints have proper `summary`, `description`, and `response_model` annotations for auto-generated OpenAPI (Swagger) docs.

### B. Database: MongoDB
* **Driver:** Use **Motor** (Asyncio driver for MongoDB).
* **ODM:** Use **Beanie** (an asynchronous ODM built on Motor and Pydantic) to ensure schema consistency between the DB and FastAPI.
* **Best Practices:**
    * Indexes must be defined in the Beanie document `Settings`.
    * No raw dictionaries; always operate on Document objects.
    * Use Environment Variables for connection strings.

### C. Frontend: React (TypeScript)
* **Build Tool:** Vite.
* **Language:** Strict TypeScript. Interfaces for all props and state.
* **State Management:** Use **Zustand** (lightweight, plays well with React Flow) or **TanStack Query** (React Query) for server state management.
* **Styling:** Tailwind CSS (utility-first).
* **Component Structure:** Functional components only using Hooks. Separate logic (custom hooks) from UI (JSX).

### D. Graph UI: React Flow
* **Customization:** Use Custom Nodes and Custom Edges for specific UI requirements. Do not rely solely on default nodes.
* **Interactivity:** Implement drag-and-drop logic and connection validation.
* **Data Sync:** The visual graph state must sync with the backend LangGraph configuration.

### E. AI Orchestration: LangChain & LangGraph
* **LangGraph:** Treat the AI workflow as a State Machine (Graph).
    * Define a global `State` TypedDict.
    * Nodes = Functions that modify the state.
    * Edges = Logic for routing between nodes.
* **Memory:** Use `Checkpointer` to persist thread history.

---

## 3. Development Commands

Use `make help` to see all available commands.

```bash
make install          # Install all dependencies
make dev              # Run backend + frontend concurrently
make dev-backend      # Run backend only
make dev-frontend     # Run frontend only
make lint             # Lint all code
make test             # Run all tests
make docker-up        # Start with Docker Compose
```

---

## 4. Coding Standards (Strict Compliance)

* **Error Handling:** Never leave a `try/catch` block empty. Log errors properly.
* **Comments:** Use Docstrings for Python functions.
* **Environment:** Create `.env.example` files. Never hardcode API keys.
* **Testing:** `pytest` (Backend) and `Vitest` (Frontend).

---

## 5. Version Control, Hygiene & Commits (CRITICAL)

**Instruction:** You must adhere to strict git hygiene. Do not treat code generation as a "dump."

### A. Atomic Commits
* **Granularity:** Do not bundle unrelated changes. Commits must be **atomic**.
    * *Bad:* "Fixed bugs and added navbar."
    * *Good:* Create two separate commits: one for the bug fix, one for the navbar.
* **Frequency:** Commit often. Do not build an entire feature in memory before generating the commit instruction.

### B. Naming Convention
* **Standard:** Strictly follow **Conventional Commits** (`type(scope): description`).
* **Types:**
    * `feat`: A new feature
    * `fix`: A bug fix
    * `docs`: Documentation only changes
    * `style`: Formatting, missing semi-colons, etc (no code change)
    * `refactor`: A code change that neither fixes a bug nor adds a feature
    * `chore`: Maintain tools, config changes (e.g., eslint, gitignore)
* **Example:** `feat(auth): implement jwt token refresh endpoint`

### C. Clean Code (No "AI Slop")
* **Comment Policy:**
    * **Prohibited:** Redundant comments describing *what* the code is doing (e.g., `// declaring variable`, `// loop through array`).
    * **Allowed:** Comments describing *why* a complex decision was made or business logic constraints.
* **Artifacts:** Do not leave placeholder comments like `// TODO: Implement this later` unless explicitly instructed to create a skeleton. Do not leave commented-out blocks of old code.

### D. Git Identity
* **No Co-Authoring:** Do not add `Co-authored-by:` trailers or references to "AI" or "ChatGPT" in the commit message body. The commit should look like it was written by a senior human engineer.

---

## 6. Execution Trigger
**Action:** Acknowledge this context. Start by proposing the **Folder Structure** for the monorepo and the **pydantic model** for the LangGraph State.
