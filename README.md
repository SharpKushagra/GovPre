# GovPreneurs Auto-Proposal System

> **AI-powered government contract proposal generation for small businesses.**
> From SAM.gov opportunity → fully compliant federal proposal draft in under 10 minutes.

---

## Features

- 🔍 **SAM.gov Ingestion** — Automatic polling every 6 hours using Celery Beat
- 📄 **Document Processing** — PDF extraction, token-based chunking (800 tokens, 150 overlap)
- 🧠 **RAG Pipeline** — pgvector similarity search + OpenAI/Gemini embeddings
- ✍️ **Proposal Generation** — 6-section structured proposals with anti-hallucination guardrails
- 📖 **Citation System** — Every paragraph includes `[Source: Solicitation Section X.Y]` references
- 🎨 **Modern UI** — 3-panel SaaS interface: opportunity details | editable editor | sources
- 📤 **Export** — PDF and Word export in one click
- 🔄 **Async Processing** — Celery workers for document processing + proposal generation

---

## Architecture

```
govpreneurs-autoproposal/
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Pydantic settings
│   ├── api/
│   │   ├── opportunities.py       # GET /opportunities, GET /opportunities/{id}
│   │   ├── proposals.py           # POST /generate-proposal, GET /proposal/{id}, POST /refine-proposal
│   │   ├── profiles.py            # CRUD for UserProfile
│   │   └── ingestion.py           # Manual ingestion triggers
│   ├── models/
│   │   ├── opportunity.py         # Opportunity + pgvector embedding
│   │   ├── document_chunk.py      # Chunked text with embeddings
│   │   ├── user_profile.py        # Company profile + embedding
│   │   └── proposal.py            # Generated proposals with JSONB sections
│   ├── schemas/                   # Pydantic request/response schemas
│   ├── services/
│   │   ├── samgov_service.py      # SAM.gov API integration + ingestion
│   │   ├── document_processor.py  # PDF extraction + chunking + embedding
│   │   ├── embedding_service.py   # OpenAI/Gemini embedding abstraction
│   │   ├── rag_service.py         # Vector search + context assembly
│   │   └── proposal_service.py    # LLM generation + section parsing
│   ├── workers/
│   │   ├── celery_app.py          # Celery + Beat configuration
│   │   └── tasks.py               # Async task definitions
│   ├── db/
│   │   └── base.py                # Async SQLAlchemy setup
│   └── alembic/                   # Database migrations
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx               # Landing page
│   │   └── proposal-review/       # 3-panel proposal interface
│   ├── features/proposal-review/
│   │   ├── ProposalReviewPage.tsx  # Main page with polling
│   │   ├── ProposalEditor.tsx      # Editable sections with AI refine
│   │   ├── OpportunityPanel.tsx    # Left sidebar
│   │   ├── SourcesPanel.tsx        # Right citations panel
│   │   ├── ProposalToolbar.tsx     # Export + tone buttons
│   │   └── GenerateModal.tsx       # 3-step proposal wizard
│   ├── lib/
│   │   ├── api.ts                 # Typed axios client
│   │   ├── store.ts               # Zustand state
│   │   └── utils.ts               # Utility functions
│   └── components/ui/             # Reusable UI components
│
└── docker-compose.yml
```

---

## Prerequisites

- Docker Desktop (recommended) **or** Python 3.11, Node.js 20, PostgreSQL 16 with pgvector, Redis
- SAM.gov API key (free at [sam.gov](https://sam.gov/content/government-api-key))
- OpenAI API key **or** Gemini API key

---

## Quick Start (Docker — Recommended)

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd govpreneurs-autoproposal
cp .env.example .env
```

Edit `.env` and fill in:
- `SAMGOV_API_KEY` — your SAM.gov API key
- `OPENAI_API_KEY` — your OpenAI key (or `GEMINI_API_KEY` if using Gemini)
- `AI_PROVIDER` — `openai` or `gemini`

### 2. Start all services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL with pgvector on port **5432**
- Redis on port **6379**
- FastAPI backend on **http://localhost:8000**
- Celery worker + Beat scheduler
- Next.js frontend on **http://localhost:3000**

### 3. Run database migrations

```bash
docker-compose exec backend alembic -c backend/alembic.ini upgrade head
```

### 4. Open the application

Visit **http://localhost:3000** and click **"Generate a Proposal"**.

---

## Local Development (Without Docker)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp ../.env.example ../.env
# Edit .env with your API keys

# Start PostgreSQL and Redis (via Docker for convenience)
docker run -d --name pgvector -e POSTGRES_USER=govpro -e POSTGRES_PASSWORD=govpro_pass -e POSTGRES_DB=govpreneurs -p 5432:5432 pgvector/pgvector:pg16
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Run migrations
alembic -c backend/alembic.ini upgrade head

# Start backend API
uvicorn backend.main:app --reload --port 8000

# In a separate terminal: start Celery worker
celery -A backend.workers.celery_app worker --loglevel=info

# In a separate terminal: start Celery Beat
celery -A backend.workers.celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Visit **http://localhost:3000**

---

## API Reference

### Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/opportunities` | List opportunities (filterable) |
| `GET` | `/opportunities/{id}` | Get single opportunity |
| `POST` | `/opportunities/{id}/process` | Queue document processing |
| `GET` | `/profiles/{id}` | Get company profile |
| `POST` | `/profiles` | Create company profile |
| `PATCH` | `/profiles/{id}` | Update company profile |
| `POST` | `/proposals/generate` | Queue proposal generation |
| `GET` | `/proposals/{id}` | Get proposal (poll for status) |
| `POST` | `/proposals/refine` | Refine a section with AI |
| `PATCH` | `/proposals/{id}/section/{section}` | Save manual edit |
| `POST` | `/ingestion/trigger-samgov` | Manually trigger SAM.gov sync |

API docs: **http://localhost:8000/docs**

---

## Proposal Generation Flow

```
User selects opportunity + company profile
           ↓
POST /proposals/generate → creates Proposal (status: pending)
           ↓
Celery task: generate_proposal_async
           ↓
RAG Pipeline:
  1. Embed user profile (OpenAI/Gemini)
  2. Vector search → top-10 relevant document chunks
  3. Build structured context with [Source: ...] metadata
  4. Call LLM (GPT-4o / Gemini 1.5 Pro) with anti-hallucination system prompt
  5. Parse JSON response → store sections in JSONB
           ↓
Proposal status → "completed"
           ↓
Frontend polls GET /proposals/{id} → renders 3-panel review UI
```

---

## SAM.gov Ingestion

The system polls SAM.gov every **6 hours** automatically via Celery Beat.

To manually trigger:
```bash
# Via API
curl -X POST http://localhost:8000/api/v1/ingestion/trigger-samgov

# Or via Celery directly
celery -A backend.workers.celery_app call backend.workers.tasks.ingest_samgov_opportunities
```

For each opportunity, the system:
1. Fetches metadata and stores in PostgreSQL
2. Generates an embedding of the description for opportunity matching
3. Queues attachment downloads for PDF processing
4. Creates 800-token chunks with 150-token overlap
5. Embeds each chunk and stores with pgvector

---

## AI System Prompt

The proposal generator uses the following exact system prompt (no modifications):

```
You are a government contract proposal writer specializing in federal solicitations.

CRITICAL RULES:
You must ONLY use information provided in the context.
DO NOT hallucinate experience, certifications, personnel, tools, or past performance.
If information is missing, explicitly state: "Information not provided in company profile."
...
```

---

## Vector Search

Uses pgvector's HNSW index for fast approximate nearest neighbor search:

```sql
SELECT *
FROM document_chunks
ORDER BY embedding <-> query_embedding
LIMIT 10
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 + pgvector |
| Migrations | Alembic |
| Task Queue | Celery 5 + Redis |
| AI | OpenAI GPT-4o + text-embedding-3-large |
| AI Alt | Gemini 1.5 Pro + text-embedding-004 |
| PDF Processing | PyMuPDF + pdfplumber |
| Tokenization | tiktoken (cl100k_base) |
| Frontend | Next.js 14, TypeScript, TailwindCSS |
| State | Zustand |
| Data Fetching | React Query (TanStack) |
| Infrastructure | Docker Compose |

---

## License

MIT — Built for the GovPreneurs platform.
