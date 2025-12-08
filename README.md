# AI Agent Backend - FastAPI with Gemini Function Calling

Production-grade FastAPI backend that powers an AI agent using Gemini function calling, custom RAG, tool integrations (Tavily search, weather API, webhook), high-quality PDF parsing & chunking, and Redis caching.

## Features

- ✅ FastAPI with async routes, CORS, global exception handling
- ✅ Gemini function calling with AUTO mode
- ✅ Custom RAG using Qdrant vector database
- ✅ Tool integrations:
  - RAG search (PDF document search)
  - Web search (Tavily)
  - Weather API
  - Webhook triggering
- ✅ Redis caching (with in-memory fallback)
- ✅ Manual chat history management
- ✅ High-quality PDF parsing with OCR fallback
- ✅ Versioned API (`/v1/...`)

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment variables:**
Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

Required API keys:
- `GOOGLE_API_KEY` - Google Gemini API key
- `LLAMAPARSE_API_KEY` - LLaMAParse API key (for PDF parsing fallback)
- `WEATHER_API_KEY` - OpenWeatherMap API key
- `TAVILY_API_KEY` - Tavily API key
- `REDIS_HOST`, `REDIS_PORT` - Redis configuration (optional, falls back to in-memory)

3. **Start services:**
- Qdrant: Make sure Qdrant is running on `localhost:6333` (or update config)
- Redis: Optional, but recommended (will fall back to in-memory if not available)

4. **Run the application:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or:
```bash
python main.py
```

## API Endpoints

### Health Check
- `GET /v1/health` - Health check endpoint

### Chat
- `POST /v1/chat` - Send chat message with Gemini function calling
  ```json
  {
    "message": "What's the weather in New York?",
    "session_id": "user123",
    "user_id": "anonymous"
  }
  ```
- `DELETE /v1/chat/{session_id}` - Clear chat history for a session

### PDF Upload
- `POST /v1/upload-pdf` - Upload and process PDF for RAG
  - Form data: `file` (PDF file)
  - Query param: `user_id` (optional)

## Project Structure

```
.
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration using pydantic-settings
├── core/
│   └── dependencies.py    # Redis client and dependencies
├── services/
│   ├── gemini_service.py  # Gemini API integration
│   ├── rag_service.py     # RAG search service
│   ├── tavily_service.py  # Web search service
│   ├── weather_service.py # Weather API service
│   ├── webhook_service.py # Webhook service
│   └── chat_history_service.py  # Chat history management
├── tools/
│   └── gemini_tools.py    # Gemini tool schemas
├── api/
│   ├── exceptions.py      # Global exception handlers
│   └── routes/
│       ├── health.py      # Health check routes
│       ├── chat.py        # Chat routes
│       └── pdf.py         # PDF upload routes
├── RAG/
│   ├── parsing_and_chunking.py  # PDF parsing & chunking
│   └── embedding_and _store.py  # Embedding & Qdrant storage
└── src/
    └── utils.py           # Utility classes (PdfExtractionResult, PageText)
```

## Usage

### Chat with Function Calling

The backend automatically uses function calling when the user's query requires it. For example:

- "Search the web for Python async best practices" → Triggers `web_search`
- "What's the weather in London?" → Triggers `get_weather`
- "Search my documents for information about X" → Triggers `rag_search`
- "Trigger a notification" → Triggers `send_webhook_event`

### Upload PDFs for RAG

Upload PDFs that will be parsed, chunked, embedded, and stored in Qdrant. Later, users can search through these documents using natural language queries.

## Configuration

All configuration is done through environment variables (see `.env.example`). The application uses `pydantic-settings` for type-safe configuration.

## Notes

- No LangChain or LangGraph dependencies
- Manual chat history management (no hidden LLM memory)
- Redis caching with automatic in-memory fallback
- Production-ready error handling and logging

