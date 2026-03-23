# Market Research Intelligence Platform — Masterplan

## 1. App Overview & Objectives

### Vision
A Market Research Intelligence Platform that empowers internal business analysts and strategy teams with AI-driven insights from diverse market research sources. The platform synthesizes information from industry reports and news feeds, identifies key trends, generates executive summaries, and provides a conversational chatbot for deep-dive Q&A — all through a unified hybrid dashboard experience.

### Primary Objectives
- **Centralize market intelligence**: Aggregate industry reports (PDFs) and real-time news into a single searchable knowledge base.
- **Automate insight generation**: Use LLM-powered RAG to identify trends, generate summaries, and produce structured reports — reducing manual research hours.
- **Enable conversational exploration**: Let analysts ask natural-language questions against the entire corpus of ingested research data.
- **Deliver actionable outputs**: Generate reports with clear, concise recommendations that directly inform strategic decision-making.

### Scope — POC / Demo
This is a **proof-of-concept** build designed to validate the core value proposition in approximately **10 hours of focused development** using Claude Code and Cowork. Production concerns like authentication, scalability, and enterprise deployment are deferred to post-POC phases.

---

## 2. Target Audience

| Attribute | Detail |
|-----------|--------|
| **Primary Users** | Internal business analysts & strategy team members |
| **Team Size (v1)** | < 10 users |
| **Technical Comfort** | Moderate — comfortable with web apps but not developers |
| **Key Need** | Faster, AI-assisted synthesis of market research to support strategic decisions |
| **Current Pain Point** | Manually reading and cross-referencing reports is time-consuming; insights are siloed across documents |

---

## 3. Core Features & Functionality

### 3.1 Document Ingestion Pipeline
- **Manual Upload**: Users can upload industry report PDFs (Gartner, McKinsey, etc.) through a drag-and-drop interface.
- **Automated News Ingestion**: Background service pulls articles from news APIs (NewsAPI, Google News RSS) on configurable topics/keywords.
- **Document Processing**: Parse PDFs (text, tables, and basic chart descriptions) and news articles into clean text chunks, generate embeddings, and store in vector database.
- **Source Metadata**: Track source name, upload date, document type, topics/tags for filtering and provenance.

### 3.2 Trend Identification
- Cross-reference multiple ingested sources to surface **recurring themes, emerging patterns, and market shifts**.
- Present trends on the dashboard with supporting source citations.
- Allow users to filter trends by time range, industry vertical, or topic.

### 3.3 Automated Executive Summaries
- On-demand generation: User selects a set of documents or a topic → system generates a concise executive summary.
- Scheduled generation: Configure recurring summaries (e.g., weekly market brief) that run automatically and appear in the dashboard.
- Summaries follow a structured template:
  - **Market Overview** — high-level landscape
  - **Key Trends** — top 3–5 identified trends with evidence
  - **Notable Developments** — significant news or report findings
  - **Actionable Recommendations** — clear next steps for the strategy team

### 3.4 Q&A Chatbot
- Conversational interface powered by RAG over the entire ingested corpus.
- Users can ask natural-language questions like:
  - *"What are the top supply chain risks mentioned across our Q1 reports?"*
  - *"Summarize what Gartner says about AI adoption in logistics."*
  - *"Compare the outlook for EV market in Europe vs. Asia."*
- Responses include **source citations** so analysts can trace back to original documents.
- Chat history preserved within session for follow-up questions.

### 3.5 Report Viewing & Export
- In-app report viewer with clean formatting.
- Export to **PDF** and **Word (.docx)** formats.
- Reports include proper headings, sections, and source attribution.

---

## 4. High-Level Technical Stack

### Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                    React Frontend                     │
│         (Dashboard + Chat Panel — Hybrid UI)          │
└──────────────┬──────────────────────┬────────────────┘
               │ REST API             │ WebSocket (chat)
┌──────────────▼──────────────────────▼────────────────┐
│                  FastAPI Backend                       │
│                                                        │
│  ┌────────────────────────────────────────────────┐    │
│  │            LlamaIndex Core Engine               │    │
│  │  ┌──────────────┐ ┌────────────┐ ┌──────────┐  │    │
│  │  │ Ingestion    │ │ Query      │ │ Report   │  │    │
│  │  │ Pipeline     │ │ Engine     │ │ Generator│  │    │
│  │  │ (LlamaParse +│ │ (RAG +     │ │ (Summary │  │    │
│  │  │  Readers)    │ │  Chat)     │ │  + Trend)│  │    │
│  │  └──────┬───────┘ └─────┬──────┘ └────┬─────┘  │    │
│  │         │               │              │        │    │
│  │  ┌──────▼───────────────▼──────────────▼─────┐  │    │
│  │  │   LlamaIndex Vector Store Index            │  │    │
│  │  │   (backed by PostgreSQL + pgvector)         │  │    │
│  │  └────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────┘    │
│                                                        │
│  ┌────────────────────┐  ┌──────────────────────────┐  │
│  │ OpenAI API         │  │ News APIs                │  │
│  │ (GPT-4o + embed)   │  │ (NewsAPI, Google News)   │  │
│  └────────────────────┘  └──────────────────────────┘  │
│                                                        │
│  ┌────────────────────┐                                │
│  │ Task Scheduler     │                                │
│  │ (APScheduler)      │                                │
│  └────────────────────┘                                │
└────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | React | Component-based, rich ecosystem for dashboards and chat UIs |
| **Backend** | FastAPI (Python) | Async-first, ideal for LLM API calls and streaming chat responses |
| **RAG Framework** | LlamaIndex | Purpose-built for document-heavy RAG; built-in ingestion, indexing, chunking, and query engines drastically reduce custom code. Hierarchical indexing and hybrid search come out of the box |
| **Document Parsing** | LlamaParse + unstructured.io | LlamaParse understands document structure (tables, multi-column layouts); unstructured.io as fallback for edge cases |
| **Database** | PostgreSQL + pgvector | Single DB for app metadata + vector embeddings via LlamaIndex's PGVectorStore integration; simple for POC, proven at scale |
| **LLM** | OpenAI GPT-4o | Strong reasoning, good at structured report generation, well-documented API; first-class LlamaIndex integration |
| **Embeddings** | OpenAI text-embedding-3-small | Cost-effective, high-quality embeddings; natively supported by LlamaIndex |
| **News APIs** | NewsAPI + Google News RSS | Free/freemium tiers available; good coverage for POC |
| **Task Scheduling** | APScheduler (in-process) | Lightweight; no need for Redis/RabbitMQ for POC. Upgrade to Celery later if needed |
| **Deployment** | Docker Compose (local) | Single command to spin up all services locally for demo |

### Why LlamaIndex Over Other RAG Frameworks

| Consideration | LlamaIndex | LangChain | Dify |
|--------------|-----------|-----------|------|
| **Document ingestion** | Built-in readers for 100+ formats via LlamaHub; LlamaParse for complex PDFs | Manual setup with document loaders | Visual builder, less control |
| **Retrieval quality** | Hierarchical indices, hybrid search (vector + keyword) out of the box | Requires manual assembly of retriever components | Pre-built but less tunable |
| **Code required for RAG** | ~30 lines for a working pipeline | ~80–100 lines for equivalent setup | Near-zero (visual), but limited customization |
| **Query engines** | Multi-document summarization, sub-queries built in | Requires chaining with LangGraph | Basic Q&A only |
| **Learning curve** | Low for RAG-focused apps | Steeper; sprawling API surface | Lowest, but hits ceiling fast |
| **Fit for this project** | ✅ Ideal — document-heavy Q&A is its sweet spot | Overkill for POC; better for complex agent workflows | Fast to demo but hard to extend into custom dashboard |

---

## 5. Conceptual Data Model

> **Note**: With LlamaIndex, the document chunks and embeddings are managed internally by the framework's indexing layer (stored in PGVectorStore). The models below represent the **application-level** data that lives alongside LlamaIndex's managed storage.

### Documents (Application Metadata)
- `id` — unique identifier
- `title` — document title
- `source_type` — enum: `pdf_upload`, `news_article`
- `source_name` — e.g., "Gartner", "Reuters", "NewsAPI"
- `original_url` — URL if from news feed; null if uploaded
- `file_path` — local storage path for uploaded PDFs
- `ingested_at` — timestamp
- `metadata` — JSON field for tags, topics, industry vertical
- `llamaindex_doc_id` — reference to LlamaIndex's internal document ID for linking retrieval results back to source

### LlamaIndex-Managed (Vector Store)
- Document nodes (chunks) with embeddings — **automatically managed by LlamaIndex's VectorStoreIndex**
- Chunk metadata (source doc, section heading, page number) — stored as node metadata within LlamaIndex
- Hierarchical index structure — enables summary-level and detail-level retrieval

### Reports
- `id` — unique identifier
- `title` — report title
- `report_type` — enum: `executive_summary`, `trend_report`, `custom`
- `content` — generated report content (markdown/HTML)
- `generated_at` — timestamp
- `is_scheduled` — boolean
- `schedule_config` — JSON for recurring schedule settings
- `source_document_ids` — array of document IDs used as input

### Chat Sessions
- `id` — unique identifier
- `started_at` — timestamp
- `messages` — JSON array of `{role, content, sources[], timestamp}`

### Trends
- `id` — unique identifier
- `title` — short trend label
- `description` — trend summary
- `confidence_score` — how strongly supported across sources
- `supporting_chunk_ids` — references to source chunks
- `identified_at` — timestamp

---

## 6. User Interface Design Principles

### Layout — Hybrid Dashboard + Chat

```
┌────────────────────────────────────────────────────────────┐
│  Top Nav: Logo | Documents | Reports | Settings            │
├──────────────────────────────────┬─────────────────────────┤
│                                  │                         │
│  MAIN PANEL (70% width)         │  CHAT PANEL (30% width) │
│                                  │                         │
│  ┌────────────────────────────┐  │  ┌───────────────────┐  │
│  │ Trend Cards / Summary      │  │  │ Chat Messages     │  │
│  │ - Key trends with badges   │  │  │ - AI responses    │  │
│  │ - Source counts            │  │  │ - Source citations │  │
│  │ - Time filters             │  │  │ - Follow-ups      │  │
│  └────────────────────────────┘  │  │                   │  │
│                                  │  │                   │  │
│  ┌────────────────────────────┐  │  │                   │  │
│  │ Recent Reports             │  │  │                   │  │
│  │ - View / Export            │  │  │                   │  │
│  └────────────────────────────┘  │  ├───────────────────┤  │
│                                  │  │ [Ask a question…] │  │
│  ┌────────────────────────────┐  │  └───────────────────┘  │
│  │ Ingested Sources Feed      │  │                         │
│  │ - Recent uploads & news    │  │                         │
│  └────────────────────────────┘  │                         │
│                                  │                         │
├──────────────────────────────────┴─────────────────────────┤
│  Status Bar: X documents indexed | Last sync: 5 min ago    │
└────────────────────────────────────────────────────────────┘
```

### Design Principles
- **Clarity over decoration**: Clean typography, generous whitespace, no unnecessary visual clutter.
- **Scannable first, detailed on demand**: Dashboard shows high-level cards; clicking drills into detail.
- **Source transparency**: Every AI-generated insight links back to its source documents.
- **Responsive chat**: Chat panel can be collapsed/expanded; supports streaming responses for a natural conversational feel.
- **Familiar patterns**: Use standard dashboard conventions (cards, tables, filters) so analysts feel productive immediately.

---

## 7. RAG Architecture & Prompt Strategy

### RAG Pipeline (Powered by LlamaIndex)

```
                    ┌─────────────────────────────┐
                    │     Document Sources          │
                    │  (PDFs, News Articles)        │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │  LlamaIndex Ingestion        │
                    │  ┌─────────────────────────┐ │
                    │  │ LlamaParse (PDFs)        │ │
                    │  │ + SimpleWebPageReader    │ │
                    │  │   (news articles)        │ │
                    │  └───────────┬─────────────┘ │
                    │  ┌───────────▼─────────────┐ │
                    │  │ Node Parser             │ │
                    │  │ (SentenceSplitter /     │ │
                    │  │  HierarchicalNodeParser)│ │
                    │  └───────────┬─────────────┘ │
                    │  ┌───────────▼─────────────┐ │
                    │  │ Embedding + Indexing     │ │
                    │  │ (OpenAI embed →          │ │
                    │  │  PGVectorStore)          │ │
                    │  └─────────────────────────┘ │
                    └──────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
   ┌──────────▼──────┐ ┌──────▼───────┐ ┌──────▼───────┐
   │ Chat Query      │ │ Summary      │ │ Trend        │
   │ Engine          │ │ Query Engine │ │ Analysis     │
   │ (RetrieverQuery │ │ (TreeSummari │ │ (Multi-doc   │
   │  + streaming)   │ │  zeIndex)    │ │  queries)    │
   └─────────────────┘ └──────────────┘ └──────────────┘
```

1. **Ingestion**: Document → LlamaParse (PDFs) or SimpleWebPageReader (news) → Automatic text extraction preserving structure (tables, headings)
2. **Chunking**: LlamaIndex's SentenceSplitter or HierarchicalNodeParser handles chunking with configurable overlap — no manual chunking code needed
3. **Indexing**: Chunks → OpenAI embeddings → PGVectorStore (pgvector) — LlamaIndex manages this end-to-end
4. **Retrieval**: User query → LlamaIndex's VectorIndexRetriever with optional hybrid search (BM25 keyword + vector similarity) → Top-k relevant nodes with metadata
5. **Generation**: Retrieved nodes + prompt template → GPT-4o → Structured response with automatic source citations via LlamaIndex's CitationQueryEngine

### Prompt Templates
The system will use **curated prompt templates** tailored for market research outputs:

- **Executive Summary Template**: Instructs the LLM to follow the structure: Market Overview → Key Trends → Notable Developments → Recommendations. Uses professional analyst tone and market research terminology.
- **Trend Identification Template**: Guides the LLM to cross-reference multiple source chunks, identify recurring themes, assess confidence levels, and present trends with supporting evidence.
- **Chatbot Q&A Template**: System prompt that establishes the assistant as a market research analyst. Instructs it to cite sources, acknowledge uncertainty, and maintain a professional but accessible tone.
- **Scheduled Brief Template**: Optimized for concise, time-bound summaries (e.g., "This week in [industry]").

### Chunking Strategy (LlamaIndex-Managed)
- **Primary parser**: `SentenceSplitter` with chunk_size=512, chunk_overlap=128 — sensible defaults for market research text
- **Advanced option**: `HierarchicalNodeParser` for documents where summary-level + detail-level retrieval is needed (e.g., long Gartner reports). This creates parent summaries and child detail chunks automatically
- **Metadata enrichment**: LlamaIndex automatically carries source document metadata through to each node. Additional metadata (source name, upload date, document type) attached via custom metadata extractors

---

## 8. Security Considerations

### POC Phase (Current)
- No authentication — open access for demo purposes.
- Application runs entirely locally via Docker Compose.
- OpenAI API key stored in `.env` file (not committed to version control).
- News API keys also in `.env`.

### Post-POC (Future Production Considerations)
- Add SSO / corporate identity provider integration (Okta, Azure AD).
- Role-based access control (admin, analyst, viewer).
- Encrypt stored documents at rest.
- Audit logging for who accessed what data and when.
- API rate limiting and input validation.
- Secure document storage (S3 with bucket policies or equivalent).
- PII/sensitive data detection in uploaded documents.

---

## 9. Development Phases & Milestones

> **Time savings with LlamaIndex**: By leveraging LlamaIndex's built-in ingestion, indexing, and query engines, the estimated development effort for the RAG pipeline drops from ~3 hours of custom code to ~1 hour of configuration. This frees up time for UI polish and feature depth.

### Phase 1: Foundation + LlamaIndex Core (Hours 1–3)
- [ ] Project scaffolding: FastAPI backend + React frontend + Docker Compose
- [ ] PostgreSQL + pgvector setup
- [ ] LlamaIndex setup: configure OpenAI LLM + embedding model, initialize PGVectorStore
- [ ] PDF upload endpoint → LlamaParse ingestion → LlamaIndex VectorStoreIndex
- [ ] Basic document listing UI + upload drag-and-drop
- [ ] **Milestone**: Can upload a PDF and see it indexed

### Phase 2: Chat & Q&A Engine (Hours 3–5)
- [ ] LlamaIndex CitationQueryEngine or RetrieverQueryEngine with streaming
- [ ] FastAPI streaming endpoint for chat (SSE or WebSocket)
- [ ] Prompt templates for Q&A with market research analyst persona
- [ ] React chat panel component with message history + source citations
- [ ] Integration of chat panel into hybrid dashboard layout
- [ ] **Milestone**: Can ask questions about uploaded documents and get cited answers

### Phase 3: Insights, Summaries & Reports (Hours 5–7)
- [ ] Executive summary generation using LlamaIndex's TreeSummarizeIndex or custom summary query
- [ ] Trend identification: multi-document query across corpus to surface recurring themes
- [ ] Report viewer component (in-app, rendered markdown)
- [ ] Export to PDF functionality
- [ ] Dashboard trend cards and recent reports section
- [ ] **Milestone**: Can generate and view an executive summary with trends

### Phase 4: News Ingestion & Scheduling (Hours 7–8.5)
- [ ] NewsAPI integration → LlamaIndex SimpleWebPageReader or custom reader
- [ ] Background scheduler (APScheduler) for periodic news pulls + re-indexing
- [ ] Scheduled report generation (e.g., weekly brief)
- [ ] Source feed display on dashboard
- [ ] **Milestone**: News articles auto-ingested and included in chat/report context

### Phase 5: Polish & Demo Prep (Hours 8.5–10)
- [ ] UI polish: loading states, error handling, empty states, responsive layout
- [ ] Status bar (document count, last sync time, index health)
- [ ] Chat UX refinements (streaming indicators, copy-to-clipboard, source links)
- [ ] End-to-end testing with real sample data (2–3 industry PDFs + live news)
- [ ] Demo walkthrough preparation
- [ ] **Milestone**: Demo-ready application

---

## 10. Potential Challenges & Mitigations

| Challenge | Impact | Mitigation |
|-----------|--------|------------|
| **Complex PDF parsing** (charts, tables, multi-column) | Lost or garbled content in knowledge base | LlamaParse handles structured documents well (tables, multi-column); fall back to `unstructured.io` for edge cases; flag problematic docs for manual review |
| **RAG retrieval quality** (wrong or irrelevant chunks returned) | Poor chatbot and summary quality | LlamaIndex supports hybrid search (BM25 + vector) out of the box; use HierarchicalNodeParser for long documents; tune chunk sizes via SentenceSplitter params |
| **LLM hallucination** | Insights not grounded in actual source data | Use LlamaIndex's CitationQueryEngine which forces source attribution; prompt templates with strict "only cite from provided context" instructions |
| **OpenAI API latency** | Slow chat responses and report generation | Use LlamaIndex's streaming support for chat; implement loading indicators; consider response caching for repeated queries |
| **10-hour time constraint** | Risk of incomplete features | LlamaIndex saves ~2 hours on RAG pipeline vs. manual implementation; strict phase milestones; news scheduling is stretch goal |
| **LlamaIndex version / API changes** | Potential breaking changes during development | Pin LlamaIndex version in requirements.txt; use stable APIs documented in official guides |
| **NewsAPI free tier limits** | Limited article ingestion volume | Cache articles aggressively; supplement with Google News RSS (no API key needed) |
| **Embedding costs** | Unexpected OpenAI billing for large document corpus | Use `text-embedding-3-small` (cheapest option); LlamaIndex handles batching automatically; set a document limit for POC |

---

## 11. Future Expansion Possibilities

### Short-Term (Post-POC)
- **Authentication & access control**: SSO integration, role-based permissions.
- **Additional data sources**: Financial filings (SEC EDGAR), social media trends, patent databases — leverage LlamaHub's 300+ data connectors.
- **Structured report frameworks**: SWOT analysis, Porter's Five Forces, PESTEL templates as selectable report types.
- **Collaborative features**: Analysts can annotate, comment on, or share reports with team members.
- **Advanced retrieval**: Enable LlamaIndex's HierarchicalNodeParser for all documents; add re-ranking with Cohere Rerank or similar.

### Medium-Term
- **Multi-LLM support**: Swap between OpenAI, Claude, or open-source models — LlamaIndex supports 50+ LLM providers via a unified interface.
- **Add LangChain for orchestration**: Introduce LangChain/LangGraph for complex multi-step agent workflows (e.g., autonomous research agents) while keeping LlamaIndex as the retrieval layer — the "hybrid stack" pattern.
- **Advanced analytics dashboard**: Time-series trend visualization, sentiment tracking, competitive landscape maps.
- **Custom alerting**: Notify analysts when new data matches their watchlist topics.
- **Feedback loop**: Analysts rate AI outputs → fine-tune prompt templates and retrieval parameters over time.
- **RAG evaluation**: Integrate RAGAS or DeepEval to systematically measure retrieval quality and answer accuracy.

### Long-Term
- **Enterprise deployment**: Cloud hosting (AWS/GCP), multi-tenant architecture, org-wide rollout.
- **Knowledge graph**: Build entity relationships (companies, markets, products) across documents for deeper cross-source analysis.
- **AI agents**: Autonomous research agents that proactively surface insights without explicit user queries.
- **API access**: Let other internal tools query the intelligence platform programmatically.

---

## 12. Key Technical Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| RAG Framework | LlamaIndex | Purpose-built for document-heavy RAG; built-in ingestion, chunking, indexing, and query engines save ~2 hours of custom code; hierarchical indexing and hybrid search out of the box |
| LLM Provider | OpenAI GPT-4o | Best-in-class reasoning; strong structured output; first-class LlamaIndex integration |
| Embedding Model | OpenAI text-embedding-3-small | Cost-effective; natively supported by LlamaIndex; same provider as LLM reduces complexity |
| Vector Storage | PostgreSQL + pgvector (via LlamaIndex PGVectorStore) | Single DB simplifies infrastructure; LlamaIndex manages the vector layer; sufficient for POC scale |
| Document Parsing | LlamaParse + unstructured.io | LlamaParse understands document structure (tables, headings); unstructured.io as fallback |
| Backend | FastAPI (Python) | Async-native; ideal for LLM streaming and API-heavy workloads; same Python ecosystem as LlamaIndex |
| Frontend | React | Rich ecosystem; best support for hybrid dashboard + chat layouts |
| News Ingestion | NewsAPI + Google News RSS | Free tiers available; good coverage for demo |
| Task Scheduling | APScheduler (in-process) | Lightweight; no external broker needed for POC |
| Deployment | Docker Compose (local) | Single-command setup; no cloud costs for demo |
| Auth | None (POC) | Defer complexity; revisit post-validation |

---

*This masterplan serves as the blueprint for building the Market Research Intelligence Platform POC. It is intended to guide development priorities, inform technical decisions, and provide a shared reference point for the team. Adjust as needed based on discoveries during implementation.*
