# Graph-Based AI Assistant

A web application for creating and orchestrating AI agent workflows using a visual graph-based interface.

## Tech Stack

- **Backend:** FastAPI, MongoDB (Motor/Beanie), LangGraph, LangChain
- **Frontend:** React, TypeScript, React Flow, Zustand, TanStack Query, Tailwind CSS
- **Infrastructure:** Docker, GitHub Actions CI/CD

## Prerequisites

- Python 3.11+
- Node.js 20+
- MongoDB (or Docker)
- [uv](https://docs.astral.sh/uv/) (Python package manager)

## Quick Start

```bash
# Install dependencies
make install

# Start development servers
make dev
```

Or with Docker:

```bash
make docker-up
```

## Development Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make install` | Install all dependencies |
| `make dev` | Run backend + frontend concurrently |
| `make dev-backend` | Run backend only (http://localhost:8000) |
| `make dev-frontend` | Run frontend only (http://localhost:5173) |
| `make lint` | Run all linters |
| `make type-check` | Run type checkers |
| `make test` | Run all tests |
| `make docker-up` | Start services with Docker Compose |
| `make docker-down` | Stop Docker services |
| `make docker-logs` | View Docker logs |
| `make build` | Build production images |
| `make clean` | Clean generated files |

## Project Structure

```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # REST endpoints
│   │   ├── core/           # Config, LLM factory
│   │   ├── models/         # Beanie documents
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic, LangGraph
│   │   └── db/             # Database connection
│   └── tests/
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── store/          # Zustand stores
│   │   ├── services/       # API client
│   │   └── types/          # TypeScript types
│   └── public/
├── docker-compose.yml       # Development environment
├── Makefile                 # Task automation
└── .env.example             # Environment template
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required for LLM features:
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key

## API Documentation

When running the backend, access the API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
