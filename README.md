# 🤖 Backend LLM API

> **REST API powered by FastAPI** that integrates with [OpenRouter](https://openrouter.ai) to provide  
> LLM-driven chat responses grounded in a local SQLite knowledge base.

![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Setup](#option-1-local-development)
  - [Docker Setup](#option-2-docker-recommended)
- [API Reference](#-api-reference)
- [Configuration](#-configuration)
- [Knowledge Base](#-knowledge-base)
- [Testing](#-testing)
- [Development](#-development)

---

## 🧠 Overview

This API acts as an **intelligent internal assistant** for a company. When a user asks a question, the system:

1. **Retrieves** relevant context from a local SQLite knowledge base using keyword matching
2. **Builds** a grounded prompt combining the internal context with the user's question
3. **Sends** the prompt to an LLM via OpenRouter
4. **Returns** a structured response with metadata about sources used

The result is an LLM that **answers using real company data first**, reducing hallucinations and providing traceable, context-aware responses.

---

## 🏗 Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────────────┐     ┌──────────────┐
│             │     │                  FastAPI Server                  │     │              │
│   Client    │────▶│                                                  │────▶│  OpenRouter   │
│  (HTTP)     │◀────│  Routes ──▶ Chat Service ──▶ OpenRouter Service  │◀────│   (LLM API)  │
│             │     │                  │                                │     │              │
└─────────────┘     │          Retrieval Service                       │     └──────────────┘
                    │                  │                                │
                    │            ┌─────┴─────┐                         │
                    │            │  SQLite   │                         │
                    │            │  (nuria.db)│                         │
                    │            └───────────┘                         │
                    └──────────────────────────────────────────────────┘
```

**Request Flow:**

```
POST /chat/ → Validate Input → Extract Keywords → Query Knowledge Base
           → Build Prompt (System + Context + User Message)
           → Call OpenRouter LLM → Return Structured Response
```

---

## 🛠 Tech Stack

| Category          | Technology                                                      |
|-------------------|-----------------------------------------------------------------|
| **Framework**     | [FastAPI](https://fastapi.tiangolo.com/) — async Python web framework |
| **LLM Provider**  | [OpenRouter](https://openrouter.ai/) — unified API for multiple LLMs |
| **Database**      | SQLite via [SQLAlchemy](https://www.sqlalchemy.org/) ORM        |
| **HTTP Client**   | [HTTPX](https://www.python-httpx.org/) — async HTTP requests    |
| **Validation**    | [Pydantic v2](https://docs.pydantic.dev/) — data validation & settings |
| **Server**        | [Uvicorn](https://www.uvicorn.org/) — ASGI server               |
| **Testing**       | [Pytest](https://docs.pytest.org/) + pytest-asyncio             |
| **Linting**       | [Ruff](https://github.com/astral-sh/ruff) — fast Python linter  |
| **Containerization** | Docker + Docker Compose                                      |

---

## 📁 Project Structure

```
backend-llm-api/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, lifespan, middleware, error handlers
│   ├── api/
│   │   └── routes_chat.py       # /health and /chat/ endpoint handlers
│   ├── core/
│   │   ├── config.py            # Centralized settings (env vars + .env)
│   │   ├── logging.py           # Structured logging setup
│   │   └── prompts.py           # System prompt templates for the LLM
│   ├── schemas/
│   │   └── chat.py              # Pydantic models: ChatRequest, ChatResponse, ErrorResponse
│   ├── services/
│   │   ├── chat_service.py      # Chat orchestration (retrieval → prompt → LLM)
│   │   ├── openrouter_service.py # OpenRouter HTTP client
│   │   └── retrieval_service.py  # Keyword-based knowledge retrieval
│   ├── db/
│   │   ├── models.py            # SQLAlchemy ORM models (KnowledgeEntry)
│   │   ├── session.py           # Database session management
│   │   └── seed.py              # Seed script for initial knowledge data
│   └── data/
│       └── seed_data.json       # Knowledge base seed entries
├── tests/
│   ├── conftest.py              # Shared fixtures (test DB, mock client)
│   ├── test_health.py           # Health endpoint tests
│   ├── test_chat.py             # Chat endpoint tests
│   └── test_retrieval.py        # Retrieval service unit tests
├── Dockerfile                   # Multi-stage Docker image
├── docker-compose.yml           # Container orchestration
├── .dockerignore                # Exclude venv, .git, secrets from build
├── requirements.txt             # Python dependencies
├── Makefile                     # Development shortcuts
├── .env.example                 # Environment variable template
├── .gitignore                   # Git exclusions
└── README.md                    # ← You are here
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.13+** (local) or **Docker** (containerized)
- An **OpenRouter API key** — [get one free here](https://openrouter.ai/keys)

### Option 1: Local Development

```bash
# 1. Clone the repository
git clone https://github.com/KafeisM/backend-llm-api.git
cd backend-llm-api

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
copy .env.example .env         # Windows
# cp .env.example .env         # macOS/Linux

# 5. Edit .env and add your OpenRouter API key
# OPENROUTER_API_KEY=sk-or-v1-your-key-here

# 6. Run the server
make run
# Or manually:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Option 2: Docker (Recommended)

```bash
# 1. Clone and configure
git clone https://github.com/KafeisM/backend-llm-api.git
cd backend-llm-api
copy .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# 2. Build and run
docker compose up --build -d

# 3. Check logs
docker logs backend-llm-api

# 4. Stop
docker compose down
```

### ✅ Verify it's running

```bash
curl http://localhost:8080/health
# → {"status":"ok"}
```

Then open the **interactive API docs**: [http://localhost:8080/docs](http://localhost:8080/docs)

---

## 📖 API Reference

### `GET /health`

Health check endpoint to verify the service is running.

**Response** `200 OK`:
```json
{
  "status": "ok"
}
```

---

### `POST /chat/`

Send a message and receive an LLM-powered response grounded in the internal knowledge base.

**Request Body:**
```json
{
  "message": "How many partners does the company have?"
}
```

| Field     | Type   | Required | Constraints        | Description               |
|-----------|--------|----------|--------------------|---------------------------|
| `message` | string | ✅       | 1–2000 characters  | The user's question       |

**Response** `200 OK`:
```json
{
  "message": "Nuria Tech Solutions has 5 founding partners: Elena Martínez (CEO), Carlos Ruiz (CTO), Ana Beltrán (COO), Jorge Navarro (CFO), and Laura Chen (VP of Engineering).",
  "model": "openrouter/free",
  "used_context": true,
  "sources": ["Partners and Leadership"]
}
```

| Field          | Type     | Description                                         |
|----------------|----------|-----------------------------------------------------|
| `message`      | string   | The LLM-generated response                         |
| `model`        | string   | Model used for generation                           |
| `used_context` | boolean  | Whether internal knowledge context was used         |
| `sources`      | string[] | Titles of knowledge entries used as context         |

**Error Responses:**

| Code | Error                     | Cause                                    |
|------|---------------------------|------------------------------------------|
| 422  | `VALIDATION_ERROR`        | Message missing, empty, or exceeds limit |
| 500  | `INTERNAL_ERROR`          | Unexpected server error                  |
| 502  | `UPSTREAM_LLM_ERROR`      | OpenRouter returned an error             |
| 502  | `UPSTREAM_UNREACHABLE`    | Cannot connect to OpenRouter             |
| 502  | `UPSTREAM_INVALID_RESPONSE` | Unexpected response format from LLM    |
| 504  | `UPSTREAM_TIMEOUT`        | OpenRouter request timed out             |

---

## ⚙ Configuration

All settings are loaded from environment variables (or a `.env` file):

| Variable              | Default                                     | Description                          |
|-----------------------|---------------------------------------------|--------------------------------------|
| `OPENROUTER_API_KEY`  | *(required)*                                | Your OpenRouter API key              |
| `OPENROUTER_MODEL`    | `meta-llama/llama-3.1-8b-instruct:free`     | LLM model to use                     |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1`              | OpenRouter API base URL              |
| `OPENROUTER_TIMEOUT`  | `30`                                        | Request timeout in seconds           |
| `APP_HOST`            | `0.0.0.0`                                   | Server bind host                     |
| `APP_PORT`            | `8080`                                      | Server bind port                     |
| `LOG_LEVEL`           | `INFO`                                      | Logging level (DEBUG/INFO/WARNING)   |
| `DATABASE_URL`        | `sqlite:///./nuria.db`                      | SQLite database path                 |

> ⚠️ **Never commit your `.env` file.** The `.gitignore` is configured to exclude it.

---

## 📚 Knowledge Base

The API uses a local SQLite database as its knowledge base. Each entry has:

| Field      | Description                                              |
|------------|----------------------------------------------------------|
| `title`    | Short descriptive title (e.g., "Vacation Policy")        |
| `content`  | Full text content of the knowledge entry                 |
| `tags`     | Comma-separated keywords for retrieval matching          |
| `category` | Grouping: `company`, `hr`, `engineering`                 |

### How Retrieval Works

1. The user's message is **normalized** (lowercase, remove accents/punctuation)
2. **Keywords** are extracted (stop words removed for both English and Spanish)
3. Each knowledge entry is **scored**: tag match = 3pts, title match = 2pts, content match = 1pt
4. The **top 3** highest-scoring entries are included as context in the LLM prompt

### Seeding Data

The database is automatically seeded on startup from `app/data/seed_data.json`. To re-seed manually:

```bash
python -m app.db.seed
```

The seed file contains 10 entries covering: company overview, leadership, employee data, HR policies, engineering processes, and internal tools.

---

## 🧪 Testing

The test suite covers health checks, chat endpoints, and the retrieval service:

```bash
# Run all tests
make test

# Or manually with verbose output
pytest tests/ -v

# Run a specific test file
pytest tests/test_chat.py -v

# Run a specific test
pytest tests/test_chat.py::test_chat_success -v
```

### Test Structure

| File                  | Coverage                                          |
|-----------------------|---------------------------------------------------|
| `test_health.py`      | Health endpoint returns `200` and correct payload |
| `test_chat.py`        | Chat flow: success, validation, error handling    |
| `test_retrieval.py`   | Keyword extraction, scoring, context retrieval    |

Tests use an **in-memory SQLite database** and **mocked OpenRouter responses** — no external API calls are made during testing.

---

## 🔧 Development

### Available Make Commands

```bash
make run          # Start dev server with hot reload
make test         # Run test suite
make lint         # Run Ruff linter
make seed         # Re-seed the knowledge database
make docker-up    # Build and start Docker container
make docker-down  # Stop Docker container
```

### Code Quality

```bash
# Lint the codebase
make lint

# Auto-fix issues
ruff check . --fix
```

### Middleware & Error Handling

The API includes:

- **Request logging middleware** — logs every request with method, path, status code, and response time
- **Validation error handler** — returns consistent `422` responses for invalid input
- **Generic exception handler** — catches unhandled errors, returns `500` without exposing stack traces

---

## 📝 License

This project is licensed under the MIT License.
