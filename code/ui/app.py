"""Streamlit chat UI over Phase 5 retrieval.

Online path (architecture.md): welcome + disclaimer + 3 examples -> guardrails
(future) -> Phase 5 retrieval -> display evidence, citation, last-updated line.

Grounded Mistral generation is not wired yet; the app runs the real Phase 5
backend and shows the retrieved evidence + one citation + transparency stamp,
ready for the generation layer to replace the evidence block.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

_CODE_DIR = Path(__file__).resolve().parents[1]
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from retrieval.pipeline import retrieve_for_query

PAGE_TITLE = "SBI Mutual Funds FAQ"

SAMPLES = (
    "What is the exit load on SBI Small Cap Fund Direct Growth?",
    "What is the lock-in for SBI ELSS Tax Saver Fund?",
    "Where do I find the expense ratio / TER for SBI Flexicap Fund?",
)


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _export_answer(question: str) -> dict:
    """Run Phase 5 retrieval and return a serializable result (no secrets)."""
    result = retrieve_for_query(question, k=5)
    result["answered_at"] = _utc_iso_now()
    return result


def _last_updated(result: dict) -> str:
    chunks = result["chunks"]
    if not chunks:
        return "Last updated from sources: unavailable"
    top = chunks[0]
    doc_date = top.get("document_date") or "not available"
    ingest = top.get("ingest_at") or result.get("answered_at", "")
    ingest_date = ingest[:10] if ingest else "?"
    return f"Last updated from sources: {doc_date} (ingested {ingest_date})"


def _citation(result: dict) -> str | None:
    chunks = result["chunks"]
    return chunks[0]["url"] if chunks else None


MAX_ANSWER_LINES = 5


def _clip_answer(answer: str) -> str:
    """Keep at most MAX_ANSWER_LINES non-empty lines of the retrieved passage."""
    lines = [ln for ln in answer.splitlines()]
    if not lines:
        return answer
    clipped = "\n".join(lines[:MAX_ANSWER_LINES]).strip()
    return clipped


def _render_chat(role: str, content: str, *, citation: str | None = None) -> None:
    with st.chat_message(role):
        st.markdown(content)
        if citation:
            st.caption(f"Citation: [{citation}]({citation})")


def _handle_question(question: str) -> None:
    question = question.strip()
    if not question:
        _render_chat("assistant", "Could you ask a factual question about one of the five SBI schemes? Here are some examples:")
        st.session_state.messages.append({"role": "assistant", "content": "Could you ask a factual question about one of the five SBI schemes? Here are some examples:"})
        return

    _render_chat("user", question)
    st.session_state.messages.append(
        {"role": "user", "content": question, "asked_at": _utc_iso_now()}
    )

    try:
        result = _export_answer(question)
    except Exception as exc:  # noqa: BLE001
        msg = f"Sorry, I hit a retrieval error: {exc.__class__.__name__}. Please try again."
        _render_chat("assistant", msg)
        st.session_state.messages.append({"role": "assistant", "content": msg})
        return

    # 6.2: no coverage -> refuse rather than guess
    if result["coverage"] == "no_coverage" or not result["chunks"]:
        body = (
            "I don't have that in this corpus. I only answer factual questions about the "
            "five SBI schemes from the public INDmoney + SBI/SEBI/AMFI documents."
        )
        cite = _citation(result)
        _render_chat("assistant", body, citation=cite)
        st.session_state.messages.append({"role": "assistant", "content": body, "citation": cite})
        return

    # 6.2 / 6.3: answer from the best retrieved passage, one citation, transparency
    top = result["chunks"][0]
    answer = _clip_answer(top["text"])
    weeks = " (weaker match)" if result["coverage"] == "weak" else ""
    body = f"{answer}{weeks}"
    note = "Facts-only. No investment advice."
    st.markdown(f"_{note}_")
    cite = _citation(result)
    _render_chat("assistant", body, citation=cite)
    st.caption(_last_updated(result))
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": body,
            "citation": cite,
            "last_updated": _last_updated(result),
        }
    )

    # Inspectable evidence: full top-k retrieval (sources/scheme/distance)
    with st.expander("Retrieved evidence (Phase 5)"):
        if result.get("ambiguous"):
            st.warning("The question did not name a clear single scheme — showing general matches.")
        if result.get("url_not_in_allowlist"):
            st.error("E11 FAILURE: citation outside the §9 allowlist")
        for i, c in enumerate(result["chunks"], start=1):
            st.markdown(
                f"**[{i}]** {c['scheme']} / {c['doc_type']} — distance {c['distance']}"
            )
            st.markdown(f"Source: [{c['url']}]({c['url']})")
            st.write(c["text"])


def _short(text: str, limit: int = 60) -> str:
    text = " ".join(text.strip().split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _render_sidebar() -> None:
    """Left-hand drawer with chat history and quick actions."""
    with st.sidebar:
        st.markdown("### 💬 Chat History")
        st.caption("Questions you asked in this session.")

        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            st.session_state.messages = []
            st.rerun()

        st.divider()

        user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
        if not user_msgs:
            st.info("No chats yet. Ask a question below to start.")
        else:
            st.caption(f"{len(user_msgs)} question(s) asked")
            for idx, m in enumerate(reversed(user_msgs), start=1):
                if st.button(
                    f"{idx}. {_short(m['content'])}",
                    key=f"hist_{idx}",
                    use_container_width=True,
                ):
                    # Persist across the rerun so the question is processed below.
                    st.session_state.pending = m["content"]
                    st.rerun()

        st.divider()

        if user_msgs:
            last = user_msgs[-1]
            st.markdown("**Last asked**")
            st.write(_short(last["content"], limit=120))
            asked_at = last.get("asked_at", "")
            if asked_at:
                st.caption(f"at {asked_at[:19].replace('T', ' ')} UTC")

        st.caption("Facts-only. No investment advice.")


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, page_icon="💰", layout="centered")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.title("SBI Mutual Funds FAQ")
    st.markdown(
        "This bot answers **factual** questions on **five SBI schemes** from public "
        "INDmoney + SBI/SEBI/AMFI documents."
    )
    st.caption("**Facts-only. No investment advice.**")

    # Clickable examples
    st.markdown("**Try an example:**")
    cols = st.columns(len(SAMPLES))
    for col, sample in zip(cols, SAMPLES):
        if col.button(sample, use_container_width=True):
            st.session_state.pending = sample

    # Render history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("citation"):
                st.caption(f"Citation: [{msg['citation']}]({msg['citation']})")
            if msg.get("last_updated"):
                st.caption(msg["last_updated"])

    # Samples / history-replay that were clicked but not yet handled
    pending = st.session_state.pop("pending", None)
    if pending:
        _handle_question(pending)

    prompt = st.chat_input("Ask a factual question about an SBI scheme…")
    if prompt:
        _handle_question(prompt)

    # Drawer last so it always reflects the latest session state.
    _render_sidebar()


if __name__ == "__main__":
    main()
