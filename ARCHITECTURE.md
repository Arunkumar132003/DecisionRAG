# Architecture Note — Northstar Workflow Copilot
**Enterprise RAG System for RFP, Compliance and Vendor-Diligence Workflows**

---

## 1. System Overview

Northstar Workflow Copilot is a production-grade Retrieval-Augmented Generation (RAG) system designed for enterprise teams answering high-stakes questions — RFPs, security audits, compliance reviews, and vendor diligence questionnaires. Every answer is grounded in authoritative source documents, carries a calibrated confidence score, cites its sources with authority rankings, and routes sensitive answers to human reviewers with a full audit trail.

The system is intentionally designed around one core principle: **never hallucinate, never over-commit, never expose sensitive data** — even when retrieval surfaces documents that contain it.

---

## 2. High-Level Data Flow

```
User Question
      │
      ▼
┌─────────────────────────┐
│   Pre-flight Checks      │  ← Sensitive request blocker, ambiguity detector
└────────────┬────────────┘
             │
      ▼
┌─────────────────────────┐
│   Hybrid Retrieval       │  ← Dense (BGE) + BM25 → RRF fusion
└────────────┬────────────┘
             │
      ▼
┌─────────────────────────┐
│   Post-retrieval Filters │  ← Domain boost, doc exclusion, secret redaction
└────────────┬────────────┘
             │
      ▼
┌─────────────────────────┐
│   BGE Cross-Encoder      │  ← Reranks top-10 → top-5 by relevance
└────────────┬────────────┘
             │
      ▼
┌─────────────────────────┐
│   LLM Answer Generation  │  ← Single Gemini call → structured JSON output
└────────────┬────────────┘
             │
      ▼
┌─────────────────────────┐
│   Governance Overlay     │  ← Deterministic rules override LLM risk decisions
└────────────┬────────────┘
             │
      ▼
┌─────────────────────────┐
│   Confidence Calibration │  ← Blends LLM score + source authority + penalties
└────────────┬────────────┘
             │
      ▼
  Structured JSON Response + Audit Log
```

---

## 3. Ingestion Layer

### 3.1 Document Parsing

Parsing is handled by **Docling**, a document intelligence library that understands document structure beyond raw text extraction. It handles:

- **PDF** — including table-only pages (tested against the Data Protection Addendum with embedded tables)
- **DOCX** — preserving heading hierarchy for context-aware chunking
- **CSV** — row-by-column flattening into readable key=value pairs
- **Markdown** and **TXT** — plain text with paragraph segmentation

For `.txt` files, a custom `_parse_txt()` builder constructs a `DoclingDocument` manually using `DocItemLabel.PARAGRAPH` per blank-line-separated block, since Docling does not natively parse raw text files.

### 3.2 Structure-Aware Chunking

Chunking uses **Docling's HybridChunker** — not a naive character or token splitter. HybridChunker is structure-aware: it respects heading boundaries, table boundaries, and paragraph breaks. Each chunk is contextualized with its parent heading chain (e.g. `Section 3 > Data Retention > Deletion Policy > …`) so the LLM receives grounded, coherent passages rather than arbitrary text windows.

- Tokenizer: `bert-base-uncased` (max 512 tokens per chunk)
- Each chunk carries heading metadata stored as a JSON string in Milvus

### 3.3 Authority Scoring

Every document is assigned an **authority score** at ingestion time — a single integer from 0–100 stored as metadata in the vector index. The formula is:

```
authority_score = STATUS_SCORE × 0.7 + TYPE_SCORE × 0.3
```

**Status scores:**

| Status | Score |
|---|---|
| approved | 100 |
| approved_reference | 80 |
| legacy | 30 |
| draft | 20 |
| informal | 10 |
| restricted | 0 |

**Type scores (selected):**

| Type | Score |
|---|---|
| security_policy | 100 |
| data_protection_addendum | 95 |
| ai_policy | 95 |
| product_faq | 90 |
| company_overview | 85 |
| release_notes | 80 |
| historical_rfp_response | 70 |
| customer_support_email | 10 |
| sensitive_data | 0 |

This means an **approved security policy** scores 100, while an **informal customer support email** scores 10. These scores flow through retrieval, context building, citation display, and confidence calibration — ensuring the entire pipeline is authority-aware, not just the prompt.

### 3.4 Storage

- **Vector index**: Milvus Lite (`.db` file) — no Docker required for local testing, same API as production Milvus
- **BM25 index**: In-memory `rank_bm25` index rebuilt from Milvus on every server startup
- **Audit trail**: Append-only JSON file at `storage/audit.json`

---

## 4. Retrieval Layer

### 4.1 Hybrid Search: Dense + BM25 + RRF

Every query triggers two parallel searches:

**Dense retrieval** — The query is embedded using `BAAI/bge-base-en-v1.5` (a top-ranked MTEB embedding model, ~109M params, runs locally with no API calls). Cosine similarity search against all stored chunk vectors in Milvus. Captures semantic meaning — "data residency" matches "where is data stored?" even with no keyword overlap.

**BM25 retrieval** — The same query is searched via Okapi BM25 keyword matching against the in-memory index. Captures exact term matches — critical for product names, model numbers, certification codes (SOC 2, ISO 27001, specific clause references).

The two ranked lists are fused using **Reciprocal Rank Fusion (RRF)**:

```
score(doc) = Σ  1 / (60 + rank_in_list)
```

Documents appearing high in both lists score highest. This is more robust than weighted score combination because it is immune to score scale differences between embedding similarity and BM25 scores.

**Top-K retrieved: 10 documents**

### 4.2 Domain-Aware Reranking

After RRF fusion, the system detects the likely domain of the question (security, privacy, AI, pricing, integration, product, release) using keyword matching. Documents whose `doc_type` matches the detected domain receive a **+20 authority point boost** before final sorting. This ensures that a security question surfaces security policies ahead of general FAQ content even if BM25 ranks them equally.

### 4.3 Document Exclusion

Before sending context to the LLM, documents with `doc_status=restricted` or `doc_type` in `{sensitive_data}` are **completely removed** from the context window. They are never seen by the model.

### 4.4 Secret Redaction

All document content passes through a regex-based secret redactor before the context string is built. Patterns matched and replaced:

| Pattern | Replacement |
|---|---|
| `sk_live_*`, `sk_test_*`, `pk_live_*` | `[REDACTED_API_KEY]` |
| `AIza*` (Google API keys) | `[REDACTED_API_KEY]` |
| `ghp_*` (GitHub tokens) | `[REDACTED_API_KEY]` |
| `password=`, `token=`, `secret=` assignments | `[REDACTED_SECRET]` |
| Credit card numbers (Luhn patterns) | `[REDACTED_CARD]` |
| SSN patterns `XXX-XX-XXXX` | `[REDACTED_SSN]` |
| Email addresses | `[REDACTED_EMAIL]` |
| Employee ID patterns `T-XXXXX` | `[REDACTED_EMPLOYEE_ID]` |

This is enforced even if the LLM prompt also instructs the model not to reveal secrets — defence-in-depth means the model literally never sees the raw values.

### 4.5 BGE Cross-Encoder Reranker

The top-10 fused documents are reranked by `BAAI/bge-reranker-v2-m3` — a cross-encoder that scores each (query, document) pair jointly, capturing query-document interaction that bi-encoder similarity cannot. All pairs are scored in a single batch call (no per-document API calls). Top-5 documents are passed to the LLM.

**Final context window: 5 documents, sorted by authority score descending, each labeled with source filename, status, and authority score.**

---

## 5. LLM Answer Generation

### 5.1 Single-Call Architecture

The system makes exactly **one LLM call per user question**. The Gemini model (`gemini-2.5-flash-lite`) receives the full context and returns a **structured JSON output** conforming to `AnswerAnalysis` — a Pydantic model with 11 fields covering answer, confidence, risk level, review flag, assumptions, missing information, citations, conflict detection, and next action.

Using `response_mime_type="application/json"` with a JSON schema enforces structured output at the API level — no fragile string parsing, no post-processing regex.

### 5.2 Prompt Design

The system prompt encodes 11 deterministic rules:

1. Answer only from provided context — never use training knowledge
2. Prefer highest-authority source when sources conflict
3. Approved documents override legacy documents
4. Informal emails cannot be used to establish commitments
5. Release notes preview features are not current commitments
6. Refuse clearly when evidence is insufficient
7. Flag SLAs, certifications, legal claims, pricing for human review
8. Never reveal secrets or PII even if present in context or explicitly requested
9. Cite only sources actually used in the answer
10. Detect and explain conflicts between sources
11. Refuse commitment questions that are not backed by approved documentation

Each context block is labeled `[SOURCE: filename | STATUS: approved | AUTHORITY: 96]` so the model can apply authority rules explicitly.

### 5.3 Confidence Calibration

The LLM's self-reported confidence score is not used directly. It is recalibrated:

```
base = llm_score × 0.6 + avg_authority_of_citations × 0.4

penalties:
  - conflicts detected:        −0.15
  - each missing info item:    −0.05  (capped at −0.20)
  - each assumption:           −0.03  (capped at −0.10)

final_score = clamp(base, 0.0, 1.0)
```

This means an answer citing only informal emails cannot score above ~0.46 regardless of LLM confidence, and an answer with detected source conflicts is automatically penalised.

---

## 6. Governance and Safety Layer

### 6.1 Pre-flight Blockers (before retrieval)

Two checks fire before any retrieval or LLM call:

**Sensitive request blocker** — Detects questions asking for API keys, tokens, credentials, passwords, OAuth secrets using regex patterns. Returns an immediate refusal with `risk_level=high`, `requires_human_review=true` — no retrieval, no LLM call, no cost.

**Ambiguity detector** — Detects questions that are too vague to answer accurately (≤3 words, "what is the policy?", "tell me about it") using heuristic patterns — no extra LLM call. Returns a clarification prompt.

### 6.2 Post-generation Governance Override

After the LLM responds, a deterministic governance engine evaluates the combined question+answer text against six pattern families: legal/contractual language, compliance certifications, security controls, pricing commitments, data handling, and sensitive data exposure. If any pattern matches, `requires_human_review` is forced to `true` regardless of the LLM's own flag — the LLM cannot override governance rules.

### 6.3 Human Review Workflow

Answers flagged for review are stored in the audit trail with `review_status=pending`. Reviewers access them via `/review/pending` and can:
- **Approve** — mark the AI answer as correct
- **Reject** — mark it wrong with a mandatory comment
- **Edit** — approve with a corrected final answer

All reviewer actions are timestamped and stored alongside the original AI answer in the audit record.

---

## 7. Audit Trail

Every chat interaction is logged to `storage/audit.json` with:

- Session ID, timestamp, question, AI answer
- Confidence score, risk level, review flag and reason
- Source citations with authority scores
- Conflict detection flag and explanation
- Assumptions and missing information lists
- Model used, retrieval latency (ms), response latency (ms)
- Review status, reviewer comment, final answer, reviewed-at timestamp

This provides a complete, immutable record of every decision the system made and every human override applied.

---

## 8. How the System Solves the Dataset Traps

| Trap | How the system handles it |
|---|---|
| **Two documents give conflicting answers** | RRF retrieval surfaces both. Authority scoring ensures the approved document scores higher in context ordering. The prompt rule explicitly instructs preference for the highest-authority source, sets `conflicts_detected=true`, populates `conflict_explanation`, and forces `requires_human_review=true`. |
| **Legacy policy contradicts newer approved policy** | Legacy documents have `STATUS_SCORE=30` vs approved's `100`. They are sorted lower in the context window. Prompt rule 3 explicitly states "approved documents win over legacy." Conflict is flagged and explained. |
| **Informal email suggests an unsafe customer commitment** | Customer support emails have `authority_score=10`. Prompt rule 4 forbids using informal emails to establish commitments. Prompt rule 11 requires that commitment questions be backed by approved documentation or refused. Governance rule additionally flags answers derived from informal sources for human review. |
| **Question has no answer in source material** | Retrieval returns low-relevance chunks. The LLM is instructed by rule 6 to say so clearly and recommend escalation. `confidence_score` is low, `missing_information` is populated, and `recommended_next_action` suggests escalation. |
| **CSV approved answer must be reconciled with policy** | Both documents are ingested and indexed. RRF retrieval can surface both. The LLM synthesises across them, and the prompt instructs it to note any discrepancy. |
| **Answer requires combining three documents** | Hybrid BM25+dense retrieval with top-10 retrieval window ensures broad coverage. RRF fusion rewards documents appearing in both lists. The structured prompt explicitly labels each source so the model can reason across them. |
| **PDF contains table-only facts** | Docling's PDF parser extracts tables into structured key=value text. The Data Protection Addendum's tables are ingested and chunked as readable content, not skipped. |
| **Release notes include planned features** | Release notes are ingested as `doc_type=release_notes` (`TYPE_SCORE=80`). Prompt rule 5 explicitly forbids presenting preview or planned features as current commitments. |
| **Sensitive data in source file** | `12_sensitive_data_sample.txt` is ingested as `doc_type=sensitive_data`, `doc_status=restricted` — giving it `authority_score=0`. It is excluded from retrieval context by the document filter. Even if it leaked through, the secret redactor strips all tokens, emails, and IDs before the context reaches the LLM. If a user asks for API keys, the pre-flight blocker refuses before retrieval even runs. |
| **Visible questions are not the final test** | No answers are hard-coded. Every question goes through the full retrieval pipeline. The system is evaluated at runtime against whatever documents are ingested. |

---

## 9. Technology Stack Summary

| Component | Technology | Reason |
|---|---|---|
| API framework | FastAPI | Async, automatic OpenAPI docs, Pydantic validation |
| Document parsing | Docling | Structure-aware, handles PDF tables, DOCX, CSV |
| Chunking | Docling HybridChunker | Heading-aware, no arbitrary splits |
| Embedding model | BAAI/bge-base-en-v1.5 | Top MTEB benchmark, runs locally, no API cost |
| Vector store | Milvus Lite | Production Milvus API, zero-infrastructure for local testing |
| BM25 | rank_bm25 | Lightweight, no server dependency |
| Retrieval fusion | RRF (manual) | Scale-independent, proven in research |
| Reranker | BAAI/bge-reranker-v2-m3 | Cross-encoder accuracy, single-batch inference |
| LLM | Gemini 2.5 Flash Lite | Fast, structured JSON output, low cost |
| Structured output | google-genai SDK + JSON schema | Enforced at API level, no parsing fragility |
| Session memory | In-process dict (ChatHistory) | Zero latency, sufficient for single-instance |
| Audit storage | JSON file | Simple, portable, zero dependencies |
| Frontend | Vanilla HTML/CSS/JS | No build step, served directly by FastAPI |
