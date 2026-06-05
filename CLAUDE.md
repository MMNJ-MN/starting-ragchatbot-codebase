# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the application

```bash
# Install dependencies (first time)
uv sync

# Set up environment
cp .env.example .env   # then add your ANTHROPIC_API_KEY

# Start the server
./run.sh
# or manually:
cd backend && uv run uvicorn app:app --reload --port 8000
```

The app is served at `http://localhost:8000`. On startup, course `.txt` files from `docs/` are automatically ingested into ChromaDB.

There are no tests or linting scripts configured in this project.

## Architecture

This is a full-stack RAG chatbot. The FastAPI backend serves both the API and the static frontend from a single process.

**Request flow for a user query:**

1. `frontend/script.js` — `sendMessage()` POSTs `{ query, session_id }` to `/api/query`
2. `backend/app.py` — creates a session if needed, delegates to `RAGSystem.query()`
3. `backend/rag_system.py` — fetches conversation history, wraps the query, calls `AIGenerator`
4. `backend/ai_generator.py` — calls Claude (turn 1) with the `search_course_content` tool available; if Claude invokes the tool, executes it and calls Claude again (turn 2) with the results to synthesize a final answer
5. `backend/search_tools.py` — `CourseSearchTool` delegates to `VectorStore.search()`, formats results, and tracks sources for the UI
6. `backend/vector_store.py` — resolves fuzzy course names via `course_catalog`, then queries `course_content` (both ChromaDB collections) with optional `course_title`/`lesson_number` filters

**Document ingestion flow:**

`docs/*.txt` → `DocumentProcessor.process_course_document()` → parses course metadata (title, link, instructor from first 3 lines) and lesson blocks (`Lesson N: Title` markers) → `chunk_text()` splits lesson content into sentence-based chunks of ~800 chars with 100-char overlap → stored in two ChromaDB collections: `course_catalog` (one doc per course) and `course_content` (one doc per chunk).

**Key design decisions:**

- Claude decides whether to search — the tool is offered with `tool_choice: auto` and the system prompt instructs one search max per query
- Course name resolution is semantic: partial/fuzzy names are vector-searched against `course_catalog` before filtering `course_content`
- Conversation history is stored in-memory only (lost on restart); `SessionManager` keeps the last 2 exchanges per session
- The `course_catalog` collection uses the course title as the ChromaDB document ID, so duplicate ingestion is prevented by checking `get_existing_course_titles()` before adding

## Course document format

Files in `docs/` must follow this structure:

```
Course Title: <title>
Course Link: <url>
Course Instructor: <name>

Lesson 1: <title>
Lesson Link: <url>
<lesson content...>

Lesson 2: <title>
...
```
