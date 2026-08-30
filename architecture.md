# Architecture: SBI Mutual Funds FAQ RAG Chatbot (Prototype)

| Field | Value |
| --- | --- |
| Source of truth | [PRD-SBI-RAG-Chatbot.md](./PRD-SBI-RAG-Chatbot.md) only |
| Type | Local prototype RAG pipeline + Streamlit UI |
| Audience | Builder / reviewer |
| Out of this doc | Anything not in the PRD (hybrid search, rerankers, auth, hosted vector DB, extra URLs, gold eval sets, SLAs) |

This architecture is the **inspectable RAG loop** the PRD requires: ingest → chunk → embed → store → retrieve → generate. Phases below are **offline ingest (1–4)** then **query-time (5–6)**. Generation, Streamlit, and product guardrails consume phase 5; they are not new data stores.

---

## Repository layout

Docs stay at `Chatbot/` root (`PRD-SBI-RAG-Chatbot.md`, this file, source brief). **Artifacts** live under `data/`. **Python** lives under `code/`. Pipeline code must not write outside `data/`.

```
Chatbot/
├── PRD-SBI-RAG-Chatbot.md
├── architecture.md
├── RAG Chatbot.txt
├── data/                          # inspectable artifacts (not source)
│   ├── uploads/                   # builder-side files mapped to source_id 1–25
│   ├── raw/
│   │   ├── html/                  # fetched/uploaded HTML
│   │   ├── pdf/                   # fetched/uploaded PDFs
│   │   └── text/                  # extracted raw_text + metadata per source_id
│   ├── skips/                     # documented 404 / empty (no URL swap)
│   ├── chunks/                    # phase 2 chunk records (url on every chunk)
│   ├── embeddings/                # phase 3 vectors sidecar (chunk_id → vector)
│   └── vector_db/                 # phase 4 local Chroma persist dir
└── code/
    ├── corpus/                    # §9 allowlist only
    ├── loading/                   # phase 1 → data/raw, data/skips
    ├── chunking/                  # phase 2 → data/chunks
    ├── embedding/                 # phase 3 → data/embeddings
    ├── vector_store/              # phase 4 → data/vector_db
    ├── retrieval/                 # phase 5
    ├── retrieval_tests/           # phase 6 (E1–E6, E11–E12)
    ├── guardrails/                # PII / empty / advice / returns
    └── ui/                        # Streamlit
```

---

## 1. System context (PRD bounds)

```
┌─────────────────────────────────────────────────────────────────┐
│ Closed corpus: 25 URLs only (PRD §9). HTML + PDF. Public only.  │
│ 5 schemes. No crawler beyond that list. 404 → skip ID, no swap. │
└──────────────────────────────┬──────────────────────────────────┘
                               │ builder ingest (not in user chat)
                               ▼
┌──────────────┐  ┌──────────┐  ┌─────────────┐  ┌───────────────┐
│ Phase 1      │→│ Phase 2  │→│ Phase 3     │→│ Phase 4       │
│ Data loading │  │ Chunking │  │ Embedding  │  │ Vector store │
└──────────────┘  └──────────┘  └─────────────┘  └───────┬───────┘
                                                         │ ChromaDB local
┌──────────────┐  ┌────────────────┐                     │
│ Streamlit UI │←│ Mistral (env)  │←──────────────┐      │
│ PRD §7       │  │ grounded gen   │              │      │
└──────┬───────┘  └────────────────┘              │      │
       │ query + samples + disclaimer             │      │
       ▼                                          │      │
┌──────────────┐  ┌────────────────┐              │      │
│ Guardrails   │→│ Phase 5        │───────────────┘      │
│ PII / empty  │  │ Retrieval     │←─ same MiniLM ───────┘
│ advice/returns│ │ logic         │
└──────────────┘  └───────┬────────┘
                          │
                          ▼
                   Phase 6 Retrieval testing
                   (PRD E1–E6, E11–E12 on retrieved chunks)
```

**Locked stack (PRD §8):** fetch/upload of §9 docs · structure-aware chunks + source URL · `sentence-transformers/all-MiniLM-L6-v2` (ingest and query) · local ChromaDB · top-k chunks only in the prompt · Mistral API key in environment · Streamlit.

**Non-architecture:** login, session history, NAV charts, user file upload, computing/comparing returns, any URL not in §9.

---

## Phase 1 — Data loading

**Purpose.** Get raw text for each of the **25 closed URLs** into a local working set so later phases never fetch “whatever is on the web.”

**Inputs**

- Hard-coded allowlist matching PRD §9 (IDs 1–25, exact URLs from the source brief / PRD).
- Builder-side **upload** of already-downloaded HTML/PDF for those IDs (PRD: ingest is offline/admin, not in the chat UI).

**Process**

1. For each ID: fetch **only** that URL, **or** load the uploaded file mapped to that ID.  
2. HTML (INDmoney scheme pages, TER page, SID/KIM repository page, SEBI HTML): extract visible text.  
3. PDF (SID, KIM, factsheets, SAI, tax reckoner, SEBI/AMFI PDFs): extract text.  
4. On **404 / empty body:** record a **documented skip** for that ID. Do **not** substitute another URL.  
5. Persist raw artifacts keyed by `source_id` (1–25) under `data/raw/` (`html/`, `pdf/`, `text/`). Skips go to `data/skips/`. Builder uploads land in `data/uploads/` mapped to the same IDs.

**Outputs (record per source)**

| Field | Why (PRD) |
| --- | --- |
| `source_id` | Closed corpus identity |
| `url` | Citation + chunk metadata |
| `scheme` | One of the five schemes, or `house` / `regulatory` for TER, SAI, tax, SEBI, AMFI, all-scheme factsheets |
| `doc_type` | scheme_page, sid, kim, factsheet, ter, sai, tax, repository, sebi, amfi |
| `raw_text` | Payload for chunking |
| `document_date` | If present in the file (factsheet month/year, etc.) |
| `ingest_at` | For `Last updated from sources:` (PRD §13: ingest date + document date when present) |
| `status` | `ok` \| `skipped` |

**Constraints.** Public sources only. No login scrape. No third-party blogs. No app screenshots.

**Phase exit.** Allowlist processed; skip log written; no extra URLs in the working set.

---

## Phase 2 — Chunking

**Purpose.** Split each loaded document so MiniLM can embed useful passages, while **every chunk keeps its source URL** (PRD §8). Prefer **document structure** (headings, SID/KIM sections) over blind fixed windows when the extract has structure.

**Inputs.** Phase 1 records with `status = ok`.

**Process**

1. Split on headings / SID-style sections when those markers exist in `raw_text`.  
2. Keep chunks **small enough for MiniLM** (short passages, not whole SIDs). Adjacent overlap is allowed only to avoid cutting a sentence that holds a fact (TER, exit load, lock-in).  
3. Attach metadata copied from the parent source; never drop `url`.  
4. If a document has no usable structure, use sequential splits of the same size budget — still with `url` on each chunk.  
5. Do not merge chunks from different `source_id`s.

**Outputs (chunk record)**

| Field | Required |
| --- | --- |
| `chunk_id` | Unique |
| `text` | Chunk body |
| `url` | **Always** the parent §9 URL |
| `source_id`, `scheme`, `doc_type` | For retrieval filters / citation / E12 scheme identity |
| `ingest_at`, `document_date` | Transparency stamp |

**PRD notes that affect this phase.** SID/KIM PDFs may be noisy; if a fact is not in a chunk, later stages **refuse** rather than invent. Midcap has **no KIM** in the corpus — Midcap facts come from SID + scheme page only.

**Phase exit.** Every chunk has `url` ∈ §9 allowlist. Chunk text is small enough to embed with `all-MiniLM-L6-v2`. Write chunk records to `data/chunks/`.

---

## Phase 3 — Embedding

**Purpose.** Turn chunk text (and later the user question) into vectors with **one** model so store and query live in the same space.

**Model (locked).** Hugging Face `sentence-transformers/all-MiniLM-L6-v2`.

**Inputs.** Phase 2 chunk `text` fields.

**Process**

1. Embed each chunk with that model only.  
2. Do not mix models, APIs, or dimensions.  
3. Query-time (phase 5) uses the **same** loaded model — no separate “query encoder.”

**Outputs.** Vector per `chunk_id`, same order/length as the model’s default output.

**Phase exit.** Every stored chunk has an embedding from this model; the query path will reuse it. Write sidecars to `data/embeddings/` (inspectable); Chroma also stores vectors in phase 4.

---

## Phase 4 — Vector store

**Purpose.** Persist embeddings + metadata locally so retrieval is ChromaDB, not ad-hoc files at query time.

**Store (locked).** **ChromaDB, local** (PRD §8). One collection for this prototype. Persist directory: `data/vector_db/`.

**What is stored per item**

- Embedding (phase 3)  
- Document text = chunk `text`  
- Metadata: `chunk_id`, `url`, `source_id`, `scheme`, `doc_type`, `ingest_at`, `document_date`

**Rules**

- Collection contains **only** chunks from §9 sources that loaded (`ok`). Skipped IDs have **no** vectors.  
- Rebuild/replace the collection from phases 1–3 when the corpus ingest is re-run; no incremental crawl of new sites.  
- No hosted/cloud vector DB. No second index.

**Phase exit.** Local Chroma collection is queryable; demo can show collection + embedding model (PRD §11.5).

---

## Phase 5 — Retrieval logic

**Purpose.** Given a user question, return **top-k chunks** from Chroma. **Only those chunks** may enter the Mistral prompt (PRD §8). Retrieval does not invent facts.

**Inputs**

- User question string (after UI / guardrail pre-checks — see below).  
- Same MiniLM model as phase 3.  
- Local Chroma collection from phase 4.

**Process**

1. Embed the question with `all-MiniLM-L6-v2`.  
2. Query Chroma for **top-k** nearest chunks (k small, prototype-scale; all k go to the prompt, nothing else).  
3. Return chunks with `text` + metadata (`url`, `scheme`, `doc_type`, dates).  
4. If the question names one of the five schemes, **prefer** chunks whose `scheme` matches (metadata filter or post-filter). If the question is ambiguous (“SBI fund”), do **not** collapse five schemes into one answer — either the top chunks are clearly one scheme, or the product asks which scheme (PRD §6.2).  
5. If top-k is empty or similarity is too weak to support a fact: signal **no coverage** so generation says the fact is not in this corpus (optional closest `url` only, no guessing).

**What retrieval is not**

- Not web search.  
- Not return calculation.  
- Not a second LLM “rewrite” of the query (not in PRD).

**Handoff to generation (PRD, not a separate store)**

Prompt (Mistral, key in env) receives: question + **only** retrieved chunk texts + instruction set from PRD: facts-only, ≤3 sentences, **one citation URL** from retrieved metadata (must be a §9 URL), `Last updated from sources:` using `ingest_at` and `document_date` when present, refuse advice, no invented numbers. If the user asked for performance comparison: do not use chunks to compute/rank; generation points at the **official factsheet URL** from the allowlist (IDs 14–16 as applicable).

**Guardrails that run before or instead of retrieval (PRD §6.2)** — not extra services:

| Check | Action |
| --- | --- |
| Empty / gibberish | No retrieve; prompt for a scheme factual question; show the three samples |
| PII (PAN, Aadhaar, account, OTP, email, phone) | Do not store; warn; do not echo secrets; retrieve only on remaining non-PII text if any |
| Buy/sell / best fund / allocation | Skip grounded “pick a fund”; refuse + **one educational corpus URL** (scheme page, SID, SAI, or tax reckoner) |
| Returns / CAGR / which performed better | No retrieve-for-ranking; **link factsheet** from §9 |

**Phase exit.** A list of k chunks (or empty/weak) with URLs in §9, ready for the prompt — or a guardrail short-circuit with no hallucinated links.

---

## Phase 6 — Retrieval testing

**Purpose.** Prove **chunks and citations** are right before calling the prototype done. This is the PRD **edge-case checklist**, not a production eval harness or gold dataset (explicitly not success in PRD §11).

**How to test retrieval itself**

For each case, run **phase 5 only** (and inspect top-k `url` / `scheme` / `text`) **and** the full answer path where the PRD specifies an answer shape.

| ID | Retrieval / citation expectation |
| --- | --- |
| **E1** TER / expense ratio for a **named** scheme | Top-k includes TER page, SID/KIM, or factsheet for **that** scheme; citation one of those URLs |
| **E2** ELSS lock-in | Chunks from ELSS SID and/or ELSS scheme page; not a different scheme’s SID |
| **E3** Min SIP | Chunks that state the number **or** empty/weak → “not in corpus”; no invented SIP |
| **E4** Exit load | SID/KIM chunks for the named scheme |
| **E5** Riskometer / benchmark | Scheme page or SID for that scheme |
| **E6** Capital-gains statement how-to | Only if text exists in loaded §9 docs; else no coverage (do not invent INDmoney app steps) |
| **E11** Hallucinated URL | Fail if any cited URL ∉ §9 allowlist (includes generation after retrieval) |
| **E12** Wrong scheme | Fail if Small Cap (etc.) numbers appear for a Large Cap question; `scheme` on retrieved chunks must match the named scheme |

**E7–E10** are **guardrail** tests (advice refusal, no return ranking, off-corpus refuse, PII). They are in the same written checklist but are not “did Chroma return the right passage” tests; they must still pass before ship (PRD §10–§11).

**Pass / fail (prototype)**

- Written checklist E1–E12.  
- Retrieval tests **fail** on wrong `scheme`, empty invent, or URL outside §9.  
- 404 skips: those IDs are absent from the index; tests that need them are N/A with the skip documented — **no replacement URL**.

**Phase exit.** Checklist filled; RAG path (Chroma + MiniLM + retrieved chunks) can be shown in a demo walkthrough.

---

## Runtime path (how phases connect)

**Offline (builder):** Phase 1 → 2 → 3 → 4.

**Online (demo user):** Streamlit (welcome, disclaimer, three examples) → guardrails → Phase 5 → Mistral (chunks only) → UI: ≤3 sentences + one citation + last-updated line. No user upload. No PII storage. No cross-session history.

**Delivery alignment with PRD slices:** Slice 1 = phases 1–5 on the five INDmoney pages; slice 2 = PDFs + metadata; slice 3 = Mistral + Streamlit; slice 4 = phase 6 + E7–E10.

---

## Decisions locked to the PRD

| Decision | Choice |
| --- | --- |
| Corpus | 25 URLs, period |
| Embeddings | `all-MiniLM-L6-v2` only, both sides |
| Index | Local ChromaDB only |
| Prompt evidence | Top-k retrieved chunks only |
| LLM | Mistral, key in env |
| UI | Streamlit, Groww-tint, facts-only copy |
| Citation | Exactly one URL, from corpus |
| Performance questions | Link factsheet; never compute |
| Advice | Refuse + educational §9 link |
