<div align="center">

# 🧠 DecisionRAG

### Enterprise-Grade AI Workflow Copilot for RFP & Compliance Automation

*Answer complex vendor-diligence, security, and compliance questions — grounded in your documents, never from hallucination.*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?style=flat-square&logo=langchain&logoColor=white)](https://langchain.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev)
[![Milvus](https://img.shields.io/badge/Milvus-2.6-00A1EA?style=flat-square&logo=milvus&logoColor=white)](https://milvus.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

[Features](#-features) · [Architecture](#-architecture) · [Tech Stack](#-tech-stack) · [Quick Start](#-quick-start) · [API Reference](#-api-reference) · [Project Structure](#-project-structure)

</div>

---

## 🎯 What is DecisionRAG?

DecisionRAG is a **production-grade Retrieval-Augmented Generation (RAG)** system built for enterprise use cases. It ingests heterogeneous document formats — PDFs, DOCX, CSVs, Markdown — and answers complex RFP, security, compliance, and vendor-diligence questions with:

- **Full source citations** with relevance scores and hierarchy ranks
- **Confidence scoring** and risk classification on every response
- **Conflict detection** between approved policies, legacy documents, and informal sources
- **Human-in-the-loop review** workflow for high-risk answers
- **Immutable audit trail** of every question, retrieval, and decision

> Built for organizations that cannot afford hallucinated answers in compliance, legal, or vendor-facing contexts.

---

## ✨ Features

### 🔍 Hybrid Retrieval Pipeline
- **Semantic search** via BGE embeddings + Milvus vector database
- **BM25 sparse search** for exact keyword matching (SLA terms, regulation names, version numbers)
- **Reciprocal Rank Fusion (RRF)** to merge both ranked lists without score normalization
- **BGE Cross-Encoder Reranker** (`BAAI/bge-reranker-v2-m3`) for final precision scoring

### 📄 Intelligent Document Ingestion
- **Docling**-powered parsing — layout-aware extraction for PDFs, DOCX, TXT, MD
- Proper table structure extraction from complex PDF documents
- Section-hierarchy-aware `HybridChunker` for semantically clean chunk boundaries
- Automatic **sensitive data detection & redaction** (PII, credentials, card numbers)
- Source hierarchy tagging — approved policies always outrank legacy documents

### 🛡️ Enterprise Safeguards
- Source trust hierarchy (approved policy > DPA > FAQ > release notes > emails > legacy)
- Conflict detection between current and legacy policy sources
- Automatic escalation for SLA, certification, legal liability, data residency questions
- Preview/planned release notes never presented as current commitments
- Sensitive trap files (`sensitive_data_sample`) blocked at ingestion — never indexed

### 🤖 Structured LLM Generation
- **Gemini 2.5 Flash Lite** via LangChain `with_structured_output()` — no JSON parsing hacks
- Pydantic-validated response schema enforced at the model level
- Temperature 0.1 for deterministic, grounded responses
- Explicit refusal when evidence is missing — zero hallucination tolerance

### 👥 Human Review Workflow
- Answers flagged `requires_human_review=true` enter a review queue
- Reviewers can approve, reject, or edit answers via API
- Approved answers can be marked for reuse in future identical queries
- Full reviewer attribution and timestamp in the audit trail

### 📊 Audit & Observability
- Every query, retrieval, generation, and review action persisted to audit log
- Retrieval latency, generation latency, and token estimates logged per query
- CSV export endpoint for batch reporting
- `/health` endpoint shows live vector index and BM25 document counts

---

## 🏗️ Architecture

<div align="center">
  <img src="https://raw.githubusercontent.com/Arunkumar132003/DecisionRAG/main/assets/decisionrag_architecture_v2.svg" width="600"/>
</div>

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **API** | FastAPI + Uvicorn | REST endpoints, async request handling |
| **LLM** | Gemini 2.5 Flash Lite | Answer generation with structured output |
| **Embeddings** | `BAAI/bge-base-en-v1.5` | Dense vector representations |
| **Reranker** | `BAAI/bge-reranker-v2-m3` | Cross-encoder precision reranking |
| **Vector DB** | Milvus (standalone via Docker) | Scalable ANN similarity search |
| **Sparse Search** | BM25 (rank-bm25) | Keyword-exact retrieval |
| **Fusion** | Reciprocal Rank Fusion | Hybrid search merging |
| **Document Parsing** | Docling | Layout-aware PDF/DOCX/MD extraction |
| **Orchestration** | LangChain + LangGraph | Chain composition, memory, routing |
| **UI** | Streamlit | Interactive front-end for QA and review |
| **Infra** | Docker Compose | Milvus + etcd + MinIO orchestration |

---

## ⚡ Quick Start

### Prerequisites

- Python 3.11+
- A Google Gemini API key ([get one free](https://ai.google.dev))

### 1. Clone the repository

```bash
git clone https://github.com/Arunkumar132003/DecisionRAG.git
cd DecisionRAG
```

### 2. Set up environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
CHAT_MODEL=gemini-2.5-flash-lite
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
MILVUS_URI=http://localhost:19530
MILVUS_COLLECTION=enterprise_rag
```

### 3. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> **Note:** First run downloads BGE embedding and reranker models (~1.5GB total). Cached after that.

### 4. Run the API

```bash
bash run.sh
# or directly:
uvicorn app:app --reload --port 8000
```

---

## 📁 Project Structure

```
DecisionRAG/
├── app.py                      # FastAPI application entry point
├── config.py                   # All settings and model config
├── docker-compose.yaml         # Milvus + etcd + MinIO services
├── run.sh                      # Startup script
├── requirements.txt
│
├── api/                        # FastAPI route handlers
│   ├── chat.py                 # /chat — single question answering
│   ├── ingest.py               # /ingest — document ingestion
│   ├── review.py               # /review — human review workflow
│   └── batch.py                # /batch — batch question processing
│
├── ingestion/                  # Document parsing & chunking
│   └── parser.py               # Docling-powered multi-format parser
│
├── retrieval/                  # Hybrid retrieval pipeline
│   ├── vectorstore.py          # Milvus dense search
│   ├── bm25_index.py           # BM25 sparse search
│   ├── hybrid.py               # RRF fusion orchestration
│   └── reranker.py             # BGE cross-encoder reranker
│
├── llm/                        # LLM generation
│   └── engine.py               # LangChain chain + structured output
│
├── memory/                     # Conversation history
│   └── history.py              # Chat history management
│
├── models/                     # Pydantic schemas
│   └── schemas.py              # Request/response models
│
├── services/                   # Business logic services
│   └── audit.py                # Audit trail logging
│
├── storage/                    # Persisted data (gitignored)
│   ├── milvus.db
│   └── audit.json
│
├── src/                        # Streamlit UI
│   └── ui.py
│
└── volumes/                    # Docker volumes (gitignored)
    ├── etcd/
    ├── minio/
    └── milvus/
```

---

## 📡 API Reference

### Document Ingestion

```bash
# Upload and index documents
POST /ingest/files
Content-Type: multipart/form-data
Body: files=@document.pdf

# Index all docs from the data/ directory
POST /ingest/directory

# Clear the entire index
POST /ingest/reset
```

### Question Answering

```bash
# Single question
POST /chat
Content-Type: application/json
{
  "question": "Does the platform support GDPR data residency in the EU?"
}

# Batch questions
POST /batch
Content-Type: application/json
{
  "questions": [
    "What is the uptime SLA?",
    "Are SOC 2 certifications available?"
  ]
}
```

### Response Schema

Every answer returns a fully structured, validated JSON object:

```json
{
  "answer": "Based on the approved Data Protection Addendum v2...",
  "confidence_score": 0.87,
  "risk_level": "high",
  "requires_human_review": true,
  "reason_for_review": "high-risk content (legal/compliance); conflicting sources detected",
  "source_citations": [
    {
      "source_file": "05_data_protection_addendum_v2.pdf",
      "source_type": "approved_dpa",
      "chunk_text": "Data shall be stored exclusively within EU...",
      "relevance_score": 0.923,
      "page_or_section": "Section 4 > Data Residency",
      "hierarchy_rank": 95
    }
  ],
  "assumptions": [],
  "missing_information": [],
  "recommended_next_action": "Route to legal team for final sign-off before RFP submission",
  "conflict_detected": false,
  "conflict_details": null,
  "sensitive_data_flagged": false,
  "model_used": "gemini-2.5-flash-lite",
  "retrieval_latency_ms": 142.5,
  "generation_latency_ms": 1823.1,
  "estimated_tokens": 2048
}
```

### Human Review Workflow

```bash
# Get answers pending review
GET /review/pending

# Approve / reject / edit an answer
POST /review/action
{
  "answer_id": 42,
  "action": "approved",           # approved | rejected | edited
  "reviewer_name": "Jane Smith",
  "reviewer_comment": "Verified against DPA v2 Section 4",
  "edited_answer": null,
  "mark_for_reuse": true
}

# Get approved answers marked for reuse
GET /review/reusable
```

### Health & Audit

```bash
GET /health
# → { "status": "ok", "semantic_chunks": 1842, "bm25_docs": 1842 }

GET /audit?limit=50&offset=0
GET /audit/{log_id}
GET /batch/export/csv
```

---

## 🔐 Source Trust Hierarchy

Documents are tagged with a trust rank at ingestion. Higher rank = more authoritative. Conflicts between sources are automatically detected and flagged.

| Source Type | Rank | Behavior |
|---|---|---|
| `approved_policy` | 100 | Highest trust; always cited first |
| `approved_dpa` | 95 | Legal agreements; triggers human review |
| `approved_ai_policy` | 92 | AI governance; overrides legacy |
| `approved_faq` | 90 | Official product answers |
| `approved_overview` | 85 | Company/product documentation |
| `approved_rfp_answers` | 80 | Pre-approved vendor responses |
| `release_notes` | 75 | Flagged: no commitment from preview features |
| `pricing_note` | 70 | Commercial terms |
| `integration_matrix` | 65 | Technical compatibility data |
| `support_emails` | 20 | Informal; flagged as unverified |
| `legacy_policy` | 10 | Superseded; conflict always flagged |
| `sensitive_trap` | 0 | **Blocked** — never indexed or returned |

---

## 🧪 Evaluation

Run the built-in evaluation harness against 14 test cases covering every assignment trap:

```bash
python evaluation/eval_harness.py
```

Test cases cover:

| Trap | Description |
|---|---|
| `sensitive_data_trap` | Credential/PII exposure prevention |
| `legacy_vs_approved` | Legacy policy must not override current |
| `sla_conflict` | Email SLA claim vs. approved policy |
| `release_notes_preview` | Preview features ≠ commitments |
| `out_of_scope_refusal` | Questions with no document evidence |
| `legal_commitment` | GDPR / data residency escalation |
| `certification_claim` | SOC 2 / ISO claims require review |
| `informal_commitment` | Support email overconfidence detection |
| `deletion_guarantee` | DPA-bound deletion timeline |
| `multi_source_synthesis` | Reconciling multiple documents |

Results saved to `evaluation/results.csv` and `evaluation/results.json`.

---


## 🔧 Configuration

All settings live in `config.py` and are overridable via `.env`:

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | required | Gemini API key |
| `CHAT_MODEL` | `gemini-2.5-flash-lite` | LLM model |
| `EMBEDDING_MODEL` | `BAAI/bge-base-en-v1.5` | Dense embedding model |
| `RERANKER_MODEL` | `BAAI/bge-reranker-v2-m3` | Cross-encoder reranker |
| `MILVUS_URI` | `http://localhost:19530` | Milvus connection |
| `MILVUS_COLLECTION` | `enterprise_rag` | Collection name |
| `TOP_K_RETRIEVAL` | `10` | Candidates per retriever |
| `TOP_K_RERANK` | `5` | Final docs after reranking |
| `CHAT_HISTORY_LIMIT` | `10` | Conversation turns to retain |

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Made with by [Arunkumar](https://github.com/Arunkumar132003)

</div>
