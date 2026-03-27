# AGENT.md

## Project Overview

This repository contains a technical backend test implementation for an entry-level backend role.

The goal is to build a **Python REST API** that exposes a chat endpoint and integrates with an LLM through **OpenRouter**, while also improving responses using a small internal knowledge source controlled by the service itself.

The project should prioritize:

- simplicity
- clarity
- reproducibility
- good backend structure
- clean documentation
- practical engineering decisions over overengineering

This is **not** intended to be a full production platform, but it should feel like a serious, well-organized backend service.

---

## Primary Goal

Build a backend service that:

- runs on **port 8080**
- exposes **POST `/chat/`**
- accepts a user message
- retrieves relevant internal context from a local knowledge source
- sends the enriched prompt to an OpenRouter free model
- returns a JSON response with at least a `message` field

---

## Non-Goals

Do **not** introduce unnecessary complexity.

Avoid adding:

- LangChain
- LlamaIndex
- vector databases
- Redis
- Celery
- PostgreSQL
- multi-agent systems
- frontend apps
- authentication unless extremely lightweight and clearly justified
- advanced infra that does not directly improve the technical test

This repository should remain easy to run and easy to review.

---

## Required Technical Decisions

Use the following stack unless there is a very strong reason not to:

- **Python 3.13**
- **FastAPI**
- **Uvicorn**
- **httpx** for OpenRouter calls
- **Pydantic** for request/response validation
- **SQLite** as local knowledge/data source
- **SQLAlchemy** is allowed, but plain sqlite usage is also acceptable if kept clean
- **python-dotenv** for environment variables
- **pytest** for tests
- **Ruff** for linting
- **Docker** for containerized execution

Preferred local dependency setup for reviewers:

- `requirements.txt`

Optional:

- `environment.yml` for personal Conda usage, but Conda must **not** be the primary setup path in the README

### Local Virtual Environment

A Python virtual environment (`venv`) is used for local development to isolate project dependencies.

The venv is located at the project root:

```text
venv/
```

**Rules for agents and local execution:**

- The venv is already created. Do **not** recreate it unless explicitly asked.
- When running Python or pip commands locally, always use the venv executables:
  - **Windows (PowerShell)**:
    - `.\venv\Scripts\python.exe` instead of `python`
    - `.\venv\Scripts\pip.exe` instead of `pip`
  - **Activation** (for interactive sessions): `.\venv\Scripts\activate`
- All `pip install` commands must target the venv to keep dependencies isolated.
- Never install packages globally for this project.

---

## Functional Requirements

The implementation must support:

### 1. Health endpoint
A lightweight endpoint such as:

- `GET /health`

Expected behavior:
- returns a simple success payload
- used to verify service status quickly

### 2. Chat endpoint
Required endpoint:

- `POST /chat/`

Expected request body:
```json
{
  "message": "How many partners does the company have?"
}
```

Expected response body:
```json
{
  "message": "..."
}
```

Optional response fields are allowed if useful, for example:
- `sources`
- `used_context`
- `model`

But the output must remain simple and easy to understand.

---

## Chat Behavior Rules

The chat flow should work like this:

1. Receive user message
2. Search the local/internal knowledge source
3. Retrieve the most relevant context
4. Build a prompt that includes:
   - system instructions
   - retrieved context
   - user question
5. Call OpenRouter
6. Return the generated response

### Important behavior constraints

- Prefer grounded answers over creative ones
- Use internal context whenever available
- If context is insufficient, answer honestly
- Avoid fabricating company-specific information not present in the local data source
- Keep answers concise and useful

### System prompt intent
The model should be guided to:
- use the provided context first
- avoid hallucinations
- say when information is unavailable
- answer clearly and professionally

---

## Internal Knowledge Source

The project should include a small local knowledge source representing private/internal company information.

This can be implemented with:

- SQLite table(s)
- seeded local records
- optionally a JSON seed file used to populate SQLite

The knowledge base should contain realistic internal-style information, for example:

- company overview
- number of partners
- employee count
- onboarding process
- how to open a Jira ticket
- vacation policy
- incident process
- internal tooling notes

The purpose is to simulate private organizational knowledge that the LLM alone would not know.

---

## Retrieval Strategy

Use a **simple retrieval strategy**.

Preferred approach:
- normalize text
- match keywords/tags/topics
- score by simple relevance
- retrieve top matching entries

This is enough for the test and preferable to adding complex vector infrastructure.

Possible future improvements can be mentioned in the README, but should not be required for the initial implementation.

---

## API and Error Handling Standards

The API should be robust and predictable.

### Validation
- validate request bodies with Pydantic
- reject invalid payloads clearly

### Error handling
Handle at least:
- invalid input
- OpenRouter upstream failures
- timeouts
- internal server errors

### Error response style
Use a consistent JSON structure for errors when practical, for example:
```json
{
  "error": "UPSTREAM_LLM_ERROR",
  "detail": "OpenRouter request failed"
}
```

### Logging
Add basic structured logging or at least clear server logs for:
- incoming requests
- retrieval decisions
- upstream failures
- startup issues

Do not log secrets.

---

## Repository Structure

Prefer a structure close to this:

```text
app/
  main.py
  api/
    routes_chat.py
  core/
    config.py
    logging.py
    prompts.py
  services/
    chat_service.py
    openrouter_service.py
    retrieval_service.py
  db/
    session.py
    models.py
    seed.py
  schemas/
    chat.py
  data/
    seed_data.json

tests/
  test_health.py
  test_chat.py
  test_retrieval.py

.env.example
README.md
requirements.txt
Dockerfile
docker-compose.yml
Makefile
```

This structure can be adjusted slightly if the separation of concerns remains clear.

---

## Configuration Rules

Use environment variables for all configurable behavior.

Minimum expected variables:

```env
OPENROUTER_API_KEY=
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
APP_HOST=0.0.0.0
APP_PORT=8080
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./nuria.db
```

Requirements:
- include `.env.example`
- never commit real secrets
- load config centrally from a config module

---

## OpenRouter Integration Rules

Use OpenRouter as the LLM gateway.

Requirements:
- use a free model
- call it through a dedicated service module
- add timeout handling
- handle non-200 responses gracefully
- isolate OpenRouter-specific logic from route handlers

The route handler should not contain raw LLM integration logic.

---

## Testing Requirements

Include at least a small but meaningful test suite.

Minimum expected tests:

- health endpoint test
- chat request validation test
- retrieval logic test
- chat flow test with OpenRouter mocked

Testing principles:
- keep tests readable
- prefer deterministic tests
- do not require real OpenRouter API access for most tests

---

## Docker Requirements

Docker support is strongly preferred.

Expected:
- `Dockerfile`
- optional `docker-compose.yml`

The containerized app must:
- run on port 8080
- be easy to start
- use environment variables cleanly

---

## README Requirements

The README is a required part of the deliverable.

It should include:

- project overview
- architecture summary
- tech stack
- setup instructions
- environment variable setup
- local run instructions
- Docker run instructions
- example API usage with `curl`
- explanation of retrieval/context approach
- testing instructions
- design decisions
- future improvements

The README should be written for a reviewer who wants to run the project quickly.

---

## Code Quality Rules

Keep the codebase simple and professional.

### Preferred qualities
- small focused modules
- type hints where useful
- clear function names
- low coupling
- no duplicated LLM logic
- clean separation between API, services, config, and data layers

### Avoid
- huge files
- business logic inside route handlers
- hardcoded secrets
- unclear abstractions
- unnecessary patterns or excessive indirection

---

## Performance and Practical Improvements

If adding small improvements, prioritize these:

- trim unnecessary context before sending to the LLM
- use reasonable request timeouts
- add lightweight caching for repeated questions only if implementation stays simple
- keep prompts concise

Do not optimize prematurely with heavy infrastructure.

---

## Definition of Done

The project is considered complete when:

- the app runs locally
- the app runs with Docker
- `GET /health` works
- `POST /chat/` works
- the chat flow uses internal retrieved context before calling OpenRouter
- errors are handled reasonably
- tests exist and pass
- `.env.example` is included
- README is complete enough for a reviewer to run the project without guesswork

---

## Implementation Order

When generating or modifying the project, follow this order:

1. create repository structure
2. implement config and environment loading
3. implement FastAPI app bootstrap
4. add `GET /health`
5. add request/response schemas
6. implement local knowledge source and seed data
7. implement retrieval service
8. implement OpenRouter service
9. implement chat orchestration service
10. implement `POST /chat/`
11. add error handling and logging
12. add tests
13. add Docker support
14. write final README

---

## Final Instruction to the Agent

When making decisions, choose the option that best balances:

- correctness
- readability
- reviewer friendliness
- minimal complexity

Do not try to impress through unnecessary architecture.
Do try to impress through clarity, grounded engineering decisions, and a polished deliverable.
