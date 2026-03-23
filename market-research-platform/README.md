# Market Research Intelligence Platform

An AI-powered market research tool that aggregates industry reports and news,
identifies trends, generates executive summaries, and enables conversational
Q&A over your entire research corpus.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React |
| Backend | FastAPI (Python) |
| RAG Framework | LlamaIndex |
| Document Parsing | LlamaParse + unstructured.io |
| Database | PostgreSQL + pgvector |
| LLM | OpenAI GPT-4o |
| Embeddings | OpenAI text-embedding-3-small |
| News Ingestion | NewsAPI + Google News RSS |
| Task Scheduling | APScheduler |
| Deployment | Docker Compose |

---

## Main Features

- **Document Ingestion** — Upload industry PDFs (Gartner, McKinsey, etc.) via drag-and-drop
- **Automated News Ingestion** — Background service pulls articles on configurable topics
- **Trend Identification** — Cross-references sources to surface recurring market themes
- **Executive Summaries** — On-demand and scheduled AI-generated briefings
- **Q&A Chatbot** — Natural-language questions answered with source citations
- **Report Export** — Export reports to PDF and Word (.docx)

---

## Setup Instructions

> TODO: Fill in after Phase 3 implementation

### Prerequisites

- Docker & Docker Compose
- OpenAI API key
- LlamaParse API key (optional, for advanced PDF parsing)
- NewsAPI key (optional, for news ingestion)

### Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd market-research-platform

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Start all services
docker-compose up --build

# 4. Open the app
# Frontend: http://localhost:3000
# Backend API docs: http://localhost:8000/docs
```

---

## Project Structure

```
market-research-platform/
├── frontend/          # React app (dashboard + chat UI)
├── backend/           # FastAPI server + LlamaIndex engine
│   ├── api/           # REST API routes
│   ├── core/          # Ingestion, query, report, scheduler
│   ├── models/        # SQLAlchemy database models
│   └── prompts/       # LLM prompt templates
├── database/          # SQL init scripts and migrations
└── docker-compose.yml # Local orchestration
```

---

*This is a proof-of-concept build. See masterplan.md for full architecture details.*
