# PRD: SBI Mutual Funds FAQ RAG Chatbot (Prototype)

| Field | Value |
| --- | --- |
| Product | Facts-only RAG FAQ assistant for 5 SBI schemes on INDmoney + official SBI/SEBI/AMFI docs |
| Status | Draft — prototype / hobby RAG test |
| Owner | PM (this doc) |
| Audience | Internal demo; not a live advisory product |
| Last updated | 30 Aug 2026 |

---

## 1. Problem

Investors looking at SBI scheme pages (Large Cap, Flexicap, ELSS Tax Saver, Midcap, Small Cap) have to hunt across INDmoney pages, SIDs, KIMs, factsheets, TER, and tax docs for basic facts (expense ratio, lock-in, SIP minimum, exit load, riskometer, statements).

We need a **small, citable, facts-only chatbot** that answers those questions from a **fixed public corpus** — and a working RAG pipeline we can inspect (ingest → chunk → embed → retrieve → generate).

This is **not** a recommendation engine and **not** a production support bot.

---

## 2. Goals

**Primary (product)**  
A user can ask a factual scheme/process question and get a short answer with **one citation URL** from the approved corpus.

**Primary (tech)**  
Prove a full RAG loop: document ingest, chunking, `all-MiniLM-L6-v2` embeddings, ChromaDB retrieval, Mistral generation, Streamlit UI.

**Non-goals for this prototype**  
Live trading, personalization, account login, return calculations, “should I buy/sell”, sources outside the 25 links below.

---

## 3. Users & jobs-to-be-done

| Who | Job |
| --- | --- |
| Curious investor (demo) | Get a factual answer + official link without reading a full SID |
| Builder / reviewer | See RAG working end-to-end and fail safely on advice / PII / out-of-corpus questions |

No authenticated user. No stored identity.

---

## 4. In scope

- **Schemes (5)**  
  - SBI Large Cap Fund (Direct Growth) — formerly BlueChip  
  - SBI Flexicap Fund (Direct Growth)  
  - SBI ELSS Tax Saver Fund (Direct Growth) — formerly Long Term Equity  
  - SBI Midcap Fund (Direct Growth)  
  - SBI Small Cap Fund (Direct Growth)

- **Corpus:** **only** the 25 URLs in §9. Nothing else (no blogs, no app screenshots, no extra pages).

- **FAQ-style factual questions**, e.g.  
  expense ratio, ELSS lock-in, minimum SIP, exit load, riskometer / benchmark, how to download a capital-gains statement (as described on public pages/docs).

- **Every answer:** one clear citation link; ≤3 sentences; line `Last updated from sources: <date or retrieval stamp>`.

- **Advice refusal:** opinion / portfolio / buy-sell questions get a polite facts-only refusal + one relevant **educational** link from the corpus (scheme page, SID, SAI, or tax reckoner as appropriate).

- **UI (Streamlit):** Groww-inspired colors; welcome line; **3 example questions**; persistent note: *Facts-only. No investment advice.*

- **Stack:** ingest (upload/fetch docs) → chunk → embed (`sentence-transformers/all-MiniLM-L6-v2`) → ChromaDB → retrieve → prompt → **Mistral API** → answer.

---

## 5. Out of scope

- Any URL not in §9  
- Performance numbers computed or compared by the bot (if asked, **link the official factsheet**, do not calculate)  
- Screenshots or private INDmoney/SBI back-end data  
- Third-party blogs, YouTube, Reddit, news  
- PII: PAN, Aadhaar, account numbers, OTP, email, phone — do not accept or store  
- Multi-turn “advisor” personality, portfolio construction, fund ranking  
- Auth, payments, “download my statement” that hits a real account  
- Production SLAs, eval harness beyond prototype edge-case checks

---

## 6. Product behavior

### 6.1 Happy path

1. User opens Streamlit app and sees welcome + 3 sample questions + facts-only disclaimer.  
2. User types a factual question (or clicks a sample).  
3. System embeds the question, retrieves the best chunk(s) from ChromaDB (same embedding model).  
4. Mistral generates an answer **grounded only in retrieved chunks**.  
5. UI shows: answer (≤3 sentences) + **one citation URL** + `Last updated from sources: …`

### 6.2 Guardrails (must)

| Situation | Behavior |
| --- | --- |
| Buy/sell/“best fund”/allocation | Refuse; no opinion; educational corpus link |
| Returns / CAGR / “which performed better” | Do not compute or compare; point to official factsheet URL |
| Question not covered by retrieved chunks | Say you don’t have it in this corpus; still offer closest citation if any, or refuse rather than guess |
| User pastes PAN/Aadhaar/account/OTP/email/phone | Do not store; tell them not to share PII; continue only on non-PII text |
| Empty / gibberish query | Ask for a scheme-related factual question; show samples |
| Ambiguous scheme (“SBI fund”) | Ask which of the 5 schemes, or answer only if retrieval is clearly one scheme |

### 6.3 Answer quality bar (prototype)

- Factual, not advisory  
- ≤3 sentences  
- One citation (the source used)  
- Transparency stamp on sources  
- English, plain language (not SID legalese dump)

---

## 7. UX (Streamlit)

**Look:** simple layout; Groww-like greens / dark-on-light (or Groww dark accent on white). Not a full Groww clone.

**Above the fold**

- Welcome: short line that this bot answers **factual** questions on **five SBI schemes** from public INDmoney + SBI/SEBI/AMFI documents.  
- Disclaimer (always visible): **Facts-only. No investment advice.**  
- Three clickable examples, e.g.  
  1. What is the exit load on SBI Small Cap Fund Direct Growth?  
  2. What is the lock-in for SBI ELSS Tax Saver Fund?  
  3. Where do I find the expense ratio / TER for SBI Flexicap Fund?

**Chat:** user input, assistant bubbles with citation + last-updated line. No file upload in the *user* chat (ingest is builder-side).

**Out of UI scope:** history across sessions, login, charts of NAV.

---

## 8. RAG / technical requirements (prototype)

| Stage | Requirement |
| --- | --- |
| Ingestion | Fetch/upload the §9 documents (HTML + PDFs). No extra crawlers. |
| Chunking | Split by document structure (headings, SID sections) where possible; keep chunks small enough for MiniLM; store **source URL** on every chunk. |
| Embedding | `sentence-transformers/all-MiniLM-L6-v2` (Hugging Face), same model at query time. |
| Vector store | ChromaDB, local for the prototype. |
| Retrieval | Top-k chunks; only those chunks go into the prompt. |
| LLM | Mistral API (key in env, not in repo). Prompt: facts-only, cite one URL, ≤3 sentences, refuse advice, no invented numbers. |
| UI | Streamlit |

**Builder ingest path:** uploading documents into the pipeline is in scope (offline / admin), not an end-user feature.

---

## 9. Corpus (closed set — 25 sources)

**INDmoney scheme pages (1–5)**  
1. [SBI Large Cap Fund Direct Growth](https://www.indmoney.com/mutual-funds/sbi-large-cap-fund-direct-growth)  
2. [SBI Flexicap Fund Direct Growth](https://www.indmoney.com/mutual-funds/sbi-flexicap-fund-direct-growth)  
3. [SBI ELSS Tax Saver Fund Direct Growth](https://www.indmoney.com/mutual-funds/sbi-elss-tax-saver-fund-direct-growth)  
4. [SBI Midcap Fund Direct Growth](https://www.indmoney.com/mutual-funds/sbi-midcap-fund-direct-growth)  
5. [SBI Small Cap Fund Direct Growth](https://www.indmoney.com/mutual-funds/sbi-small-cap-fund-direct-plan-growth)

**SBI SID / KIM (6–13)**  
6. SBI BlueChip SID  
7. SBI BlueChip KIM  
8. SBI Flexicap SID  
9. SBI Flexicap KIM  
10. SBI Long Term Equity / ELSS SID  
11. SBI Small Cap SID  
12. SBI Small Cap KIM  
13. SBI Magnum Midcap SID  

(Use the exact `sbimf.com` PDF URLs from the source brief.)

**Factsheets / fees / tax (14–20)**  
14. SBI ELSS Tax Saver — Jan 2026 factsheet  
15. All-scheme comparative factsheet — Feb 2026  
16. All-scheme Direct Plan factsheet — Jan 2026  
17. [Total Expense Ratio](https://www.sbimf.com/total-expense-ratio)  
18. Statement of Additional Information (SAI)  
19. Tax Reckoner FY 2026–27  
20. [SID / KIM repository](https://www.sbimf.com/offer-document-sid-kim)

**SEBI / AMFI (21–25)**  
21. SEBI mutual fund filings index  
22. SEBI SBI MF fund details  
23. SEBI scheme categorisation (Feb 2026 PDF)  
24. SEBI SBI MF disclosure document  
25. AMFI SBI scheme document (`portal.amfiindia.com/spages/4675.pdf`)

**Corpus rule:** if it is not in this list, it is not in the index.

---

## 10. Edge-case test plan (must run before calling the prototype “done”)

| ID | Case | Expected |
| --- | --- | --- |
| E1 | Expense ratio / TER for one named scheme | Short fact + TER or SID/KIM/factsheet citation |
| E2 | ELSS lock-in | 3-year (or SID wording) + ELSS SID or scheme page |
| E3 | Min SIP | Number from corpus + citation; if missing, “not in corpus” |
| E4 | Exit load | Fact + SID/KIM |
| E5 | Riskometer / benchmark | Fact + scheme page or SID |
| E6 | Capital-gains statement “how to” | Process from public docs/pages only + one link |
| E7 | “Should I buy SBI Small Cap?” | Refusal + educational link; no recommendation |
| E8 | “Which of these 5 gave best returns?” | No ranking/compute; factsheet link |
| E9 | Unrelated (weather, cricket) | Refuse; stay on corpus |
| E10 | PII in the box | No persist; warn; no echo of secrets |
| E11 | Hallucinated URL | Fail if answer cites a URL not in §9 |
| E12 | Wrong scheme facts (e.g. Small Cap numbers for Large Cap) | Fail; retrieval/prompt must keep scheme identity |

---

## 11. Success criteria (prototype)

**Ship when:**

1. All 25 sources ingest (or documented skip if a URL 404s — then drop that ID, do not substitute a new URL without a PRD update).  
2. Streamlit UI matches §7.  
3. E1–E12 pass on a written checklist.  
4. No answer without a corpus citation on factual path; advice path never gives a buy/sell.  
5. RAG path is visible (Chroma collection + embedding model + Mistral) for a demo walkthrough.

**Explicitly not success:** accuracy vs a gold dataset, latency SLOs, or SEBI-compliant “investment advisor” positioning.

---

## 12. Risks & compliance (plain language)

- **Regulatory:** this is a **document Q&A demo**, not advice. Disclaimer must stay on screen.  
- **Stale data:** factsheets are dated; always show last-updated-from-sources.  
- **PDF quality:** SID/KIM chunking may be noisy — prefer structured splits; if a fact isn’t in a chunk, refuse rather than invent.  
- **API keys:** Mistral key in environment only.  
- **INDmoney / SBI ToS:** public pages/PDFs only; no scraping behind login.

---

## 13. Open questions (PM — resolve while building)

1. Exact “Last updated from sources” format: ingest date vs document date on the PDF? **Recommendation:** show ingest date + document title/date when present in metadata.  
2. Midcap KIM is not in the original 13 SID/KIM list — if a question needs KIM-only Midcap text, answer from SID + scheme page or say not in corpus.  
3. “How to download capital-gains statement” may live on INDmoney UX not fully in HTML — if not in corpus text, refuse with closest public help link from §9 only.

---

## 14. Delivery slices (suggested)

| Slice | Outcome |
| --- | --- |
| 0 | This PRD + closed URL list in code |
| 1 | Ingest 5 INDmoney pages + Chroma + retrieval smoke test |
| 2 | PDFs (SID/KIM/factsheets) + metadata (url, scheme, doc type) |
| 3 | Mistral prompt + guardrails + Streamlit Groww-tint UI |
| 4 | Edge-case checklist E1–E12 |

---

## Appendix A — Sample product copy

**Welcome**  
Ask factual questions about five SBI mutual fund schemes using public INDmoney pages and official SBI, SEBI, and AMFI documents.

**Disclaimer**  
Facts-only. No investment advice.

**Advice refusal (example)**  
I can’t recommend buying or selling. I only share facts from the scheme documents. You can read the official scheme information here: \<one corpus URL\>.
