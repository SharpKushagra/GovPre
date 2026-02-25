## GovPreneurs Auto-Proposal – Case Study Submission

**Role**: AI Product Management Intern  
**Company**: GovPreneurs  
**Feature**: Auto-Proposal Engine

> Replace the placeholders below with your actual links before submitting.

- **Loom Video**: `TODO – paste Loom URL here`
- **Prototype Link** (Lovable / v0 / Figma / deployed app): `TODO – paste prototype URL here`

---

## Part 1 – Data Integration Strategy (The “Plumbing”)

### 1.1 SAM.gov Source Analysis

The system integrates with the SAM.gov Opportunities API (v2) and focuses on:

- **Opportunity identity**: `noticeId`, `solicitationNumber`, `title`, `notice_type`
- **Agency context**: `department`, `agency`, `sub_agency`
- **Business fit**:
  - **NAICS**: `naics_code`, `naics_description`
  - **Set-Aside**: `set_aside_type` (e.g., SDVOSB, WOSB, 8(a))
  - **Contract type**: `contract_type`, `estimated_value`
  - **Place of performance**: `place_of_performance`
- **Lifecycle**:
  - `posted_date`, `response_deadline`, `archive_date`
  - `last_modified_date`, `active`
- **RFP content**:
  - `description` field from the listing
  - attached PDFs via SAM.gov `resourceLinks` / attachments API

### 1.2 “GovPreneurs Opportunity” JSON Schema

This schema mirrors the backend `Opportunity` Pydantic models and is optimized for:

- **Matching**: NAICS, set-aside, geography, and value range
- **RAG**: a `full_text` field that aggregates the most relevant description/SOW text
- **Freshness**: dates and `last_modified_date` for delta updates

```json
{
  "$id": "https://govpreneurs.app/schemas/opportunity.json",
  "title": "GovPreneursOpportunity",
  "type": "object",
  "required": ["id", "notice_id", "title", "active", "created_at", "updated_at"],
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "notice_id": { "type": "string", "description": "Stable SAM.gov noticeId" },
    "title": { "type": "string" },
    "description": { "type": ["string", "null"] },

    "agency": { "type": ["string", "null"] },
    "sub_agency": { "type": ["string", "null"] },
    "department": { "type": ["string", "null"] },

    "posted_date": { "type": ["string", "null"], "format": "date-time" },
    "response_deadline": { "type": ["string", "null"], "format": "date-time" },
    "archive_date": { "type": ["string", "null"], "format": "date-time" },
    "last_modified_date": { "type": ["string", "null"], "format": "date-time" },

    "notice_type": { "type": ["string", "null"] },
    "solicitation_number": { "type": ["string", "null"] },

    "naics_code": { "type": ["string", "null"] },
    "naics_description": { "type": ["string", "null"] },
    "set_aside_type": {
      "type": ["string", "null"],
      "description": "e.g., SDVOSB, WOSB, 8(a), Small Business"
    },

    "place_of_performance": { "type": ["string", "null"] },
    "contract_type": { "type": ["string", "null"] },
    "estimated_value": { "type": ["string", "null"] },

    "attachments": {
      "type": ["array", "null"],
      "items": {
        "type": "object",
        "required": ["file_name", "file_url", "file_type"],
        "properties": {
          "file_name": { "type": "string" },
          "file_url": { "type": "string", "format": "uri" },
          "file_type": { "type": "string" }
        }
      }
    },

    "full_text": {
      "type": ["string", "null"],
      "description": "Aggregated description/SOW used for embeddings and matching"
    },

    "active": { "type": "boolean", "default": true },

    "created_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" }
  }
}
```

**Why these fields matter for AI evaluation**

- **NAICS / Set-Aside**: enable hard filters so we never suggest opportunities the user is ineligible for.
- **Deadlines & archive date**: prevent drafting proposals on expired or archived opportunities.
- **Place of performance & agency**: let us bias towards local work and agencies the user has past performance with.
- **Estimated value & contract type**: enable better prioritization (fit-to-size, FFP vs T&M, etc.).
- **Attachments & full_text**: give the RAG pipeline high-signal context from the SOW and instructions.

### 1.3 Ingestion & Freshness Strategy

**Mechanism**

- **Scheduled polling (Celery Beat)** every **6 hours**:
  - `run_full_ingestion` calls `fetch_opportunities(limit=100, offset=…)` on SAM.gov.
  - New opportunities are stored via `store_opportunity`, which:
    - maps fields with `_extract_opportunity_data`
    - computes an **embedding of `full_text`** for matching.
- **Delta updates** using `modifiedFrom`:
  - `fetch_modified_opportunities(modified_from=…)` pulls recently changed notices.
  - `update_opportunity` compares `last_modified_date` and only updates when newer.
  - On change, it **re-embeds** `full_text` so vector search stays aligned.
- **Expiry handling**:
  - `mark_expired_inactive` flips `active=false` once `archive_date` is in the past.

**Why polling vs webhooks?**

- SAM.gov does not expose first-class webhooks for this workflow; polling is:
  - **Predictable**: Celery Beat handles retries, backoff, and observability.
  - **Control-friendly**: we can tune polling by notice type, NAICS, or size.

**Handling “deadline changed yesterday”**

- The `modifiedFrom`-based delta run ensures:
  - Any change to `response_deadline` or `archive_date` flows through `update_opportunity`.
  - Frontend always reads from our DB, so users see the **current** deadline and active/inactive status.

---

## Part 2 – RAG Workflow & Prompt Engineering (The “Brain”)

### 2.1 RAG Pipeline – High-Level Steps

Scenario: **SafeGuard Security** wants to apply to an ingested solicitation with a PDF attachment.

1. **Ingestion**
   - SAM.gov opportunity and attachments are ingested as described above.
   - PDFs are downloaded, chunked (≈800 tokens with 150-token overlap), embedded, and stored in `document_chunks` with `opportunity_id` and `source_file`.
2. **User context**
   - SafeGuard’s **company profile** (capabilities statement, past performance, NAICS, set-asides, certifications, etc.) is stored in `UserProfile`.
3. **Profile embedding**
   - `RAGService.embed_user_profile` builds a single profile document (company, NAICS, set-asides, capabilities, past performance) and embeds it.
4. **Targeted retrieval**
   - `retrieve_opportunity_chunks` runs a **vector search within that opportunity’s chunks**:
     - `SELECT … FROM document_chunks WHERE opportunity_id = :id ORDER BY embedding <-> :query_embedding LIMIT N`
   - This ensures we pull only the relevant requirement text from the specific RFP.
5. **Structured context assembly**
   - `build_structured_context` creates:
     - `solicitation_context`: concatenated chunks, each prefixed with a **machine-readable citation** (`[Source: …]`).
     - `user_profile_context`: the profile document.
     - `sources`: an array of `{ chunk_id, snippet, citation, source_file, similarity }` for use in the UI.
6. **Proposal generation**
   - `ProposalService.generate_proposal`:
     - builds a user prompt via `_build_generation_prompt(context, tone)`
     - calls the LLM with a **strict system prompt** (below)
     - parses JSON into six sections (`executive_summary`, `technical_approach`, etc.) and **attaches sources**.
7. **Review + refinement**
   - The frontend renders:
     - left: opportunity details
     - center: editable proposal sections
     - right: sources/citations panel
   - Section-level **refinement** uses `refine_section` to re-run the LLM on a single section with user instructions.

### 2.2 Chunking & Retrieval Details

- **Chunking strategy**
  - Target size: ~**800 tokens**, **150-token overlap**.
  - Preserves paragraph boundaries where possible to avoid cutting mid-requirement.
- **Why profile → query embedding?**
  - The user profile often encodes what the company can do; using it as the query emphasizes:
    - requirements that match their capabilities and past performance
    - sections where they are likely to be compliant and competitive.
- **Mitigating hallucinations**
  - Retrieval is **opportunity-scoped** (by `opportunity_id`).
  - The system prompt forbids hallucinated experience and forces “Information not provided…” when data is missing.

### 2.3 System Prompt (Exact)

This is the exact system prompt used by the backend (`SYSTEM_PROMPT` in `proposal_service.py`):

```text
You are a government contract proposal writer specializing in federal solicitations.

CRITICAL RULES:

You must ONLY use information provided in the context.

DO NOT hallucinate experience, certifications, personnel, tools, or past performance.

If information is missing, explicitly state:
"Information not provided in company profile."

Tone must be:
- Professional
- Formal
- Government-compliant
- Clear
- Concise
- Evidence-based

You must:
- Match company capabilities to solicitation requirements
- Cite relevant experience
- Follow federal proposal structure
- Use realistic compliance language

Output format: Return a valid JSON object with these exact keys:
{
  "executive_summary": {"content": "...", "sources": [{"citation": "..."}]},
  "technical_approach": {"content": "...", "sources": [{"citation": "..."}]},
  "past_performance": {"content": "...", "sources": [{"citation": "..."}]},
  "compliance_matrix": {"content": "...", "sources": [{"citation": "..."}]},
  "company_overview": {"content": "...", "sources": [{"citation": "..."}]},
  "conclusion": {"content": "...", "sources": [{"citation": "..."}]}
}
```

**Why this prompt is pragmatic**

- **Anti-hallucination**: explicitly forbids invented experience and instructs the model to surface missing data.
- **Compliance-first**: pushes towards formal, government-style language and structure.
- **Citations**: the model must attach sources, which we align with RAG sources for UI trust.
- **Structured JSON**: makes parsing robust and enables a clean, sectioned editor in the frontend.

---

## Part 3 – Design & “Lovable” UI (The Experience)

### 3.1 Proposal Review Screen – Layout

The implemented UI in `frontend/features/proposal-review` corresponds directly to the requested screen:

- **3-panel layout**
  - **Left – Opportunity Panel** (`OpportunityPanel`):
    - Status, deadlines, agency, NAICS, set-asides, contract details, place of performance, attachments, and description.
  - **Center – Proposal Editor** (`ProposalEditor`):
    - Tabbed navigation for the six proposal sections.
    - Inline editing and AI-powered refinement per section.
  - **Right – Sources Panel** (`SourcesPanel`):
    - Active-section citations and snippets.
    - “All References” grouped by section.

### 3.2 Trust – “Did the AI Make This Up?”

- **Inline citations**
  - Proposal text includes `[Source: …]` tags inside each section.
  - Clicking a tag:
    - highlights the corresponding source in the **Sources Panel**
    - shows a short snippet of the original chunk in a card.
- **Sources Panel**
  - Shows citation label, snippet, and (when available) originating file name.
  - Active section vs. all references are visually separated.
- **Attachment links**
  - The Opportunity Panel lists attachments with direct links back to SAM.gov files.

This makes it clear *where* each claim in the proposal came from and allows the user to quickly cross-check.

### 3.3 Iterative Refinement – “Change Tone” / “Expand This”

- **Global tone control**
  - A **tone selector** in `ProposalToolbar` (e.g., professional / assertive / concise / detailed) sets `selectedTone` in state.
  - Subsequent generations/refinements use this tone in `_build_generation_prompt`.
- **Section-level AI refine**
  - In `ProposalEditor` each section has:
    - a **wand icon** that toggles a “Refine this section with AI” panel.
    - a freeform instruction textbox (e.g., “Make this more concise and highlight our guard force experience”).
    - a “Refine” button that calls `POST /proposals/refine`.
  - While refining, we show a shimmering skeleton to make the async work feel responsive.
- **Manual edits + autosave**
  - Users can edit any section manually in a textarea and save changes back to the backend (`PATCH /proposals/{id}/section/{section}`).

### 3.4 “Lovable” Factor – Modern, Encouraging SaaS

Design choices to avoid “clunky government portal” UX:

- **Visual language**
  - Soft **Gov-blue** palette (buttons, highlights, headers) with subtle gradients and glows.
  - Rounded cards, subtle shadows, and animated loading states.
- **Microcopy**
  - Friendly, confidence-building copy (“AI is Writing Your Proposal”, “Generate Your First Proposal”).
- **State-specific screens**
  - Dedicated empty, loading, generating, and error states with icons and clear guidance.

**Prototype Link**

- Replace with the best representation of this UI:
  - Deployed frontend, or
  - Lovable.dev / v0.dev / Figma file that mirrors this layout.

`Prototype URL: TODO – paste here`

---

## Part 4 – The Pitch (Video)

Use the Loom video to tell a simple, user-focused story:

### 4.1 Suggested 3–5 Minute Script

1. **Intro (30–45s)**
   - Who you are.
   - Problem statement: “Going from SAM.gov opportunity to first draft proposal takes days.”
2. **Data Schema & Ingestion (60s)**
   - Briefly show the **GovPreneurs Opportunity** schema.
   - Explain why NAICS, set-asides, deadlines, and full_text matter for matching & AI.
   - Describe the **6-hour polling + modifiedFrom** strategy and how deadline changes are handled.
3. **RAG Logic & Prompt (60–90s)**
   - Walk through the RAG steps: profile → embedding → opportunity-scoped vector search → structured context → JSON output.
   - Call out the **anti-hallucination rules** and the “Information not provided…” behavior.
4. **Prototype Demo (60–90s)**
   - Show the Proposal Review Screen:
     - Click citations and show the Sources Panel snippets.
     - Change tone and refine a section with a natural-language instruction.
     - Export to PDF/Word.
   - Emphasize how this makes the user feel **in control** and **confident** in the AI.
5. **Closing (15–30s)**
   - Reiterate impact: “From RFP to draft proposal in under 10 minutes, with trust and control built in.”

### 4.2 Loom Link

- `TODO – paste Loom URL here`

---

## How to Use This Document

- **For Notion**: paste this markdown into a Notion page, fill in the `TODO` links, and adjust any wording to your voice.
- **For PDF**: export the Notion page (or this markdown rendered locally) as PDF and attach it as the main submission artifact.

