"""Streamlit chat UI over Phase 5 retrieval.

Online path (architecture.md): welcome + disclaimer + 3 examples -> guardrails
(future) -> Phase 5 retrieval -> display evidence, citation, last-updated line.

The app runs the real Phase 5 backend and shows the retrieved evidence + one
citation + transparency stamp. UI extras: styled brand header, chat-history
drawer, EN/HI language toggle, dark/light theme switch, and A-/A+ text sizing.
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

BRAND = "SBI Mutual Funds Chat-bot"

_UI_DIR = Path(__file__).resolve().parent
LOGO_PATH = _UI_DIR / "Logo.png"
_HAS_LOGO = LOGO_PATH.is_file()

EXAMPLES = (
    {
        "q": "What is the exit load on SBI Small Cap Fund Direct Growth?",
        "label_en": "What is the exit load on SBI Small Cap Fund Direct Growth?",
        "label_hi": "SBI Small Cap Fund पर exit load क्या है?",
    },
    {
        "q": "What is the lock-in for SBI ELSS Tax Saver Fund?",
        "label_en": "What is the lock-in for SBI ELSS Tax Saver Fund?",
        "label_hi": "SBI ELSS Tax Saver Fund की lock-in अवधि क्या है?",
    },
    {
        "q": "Where do I find the expense ratio / TER for SBI Flexicap Fund?",
        "label_en": "Where do I find the expense ratio / TER for SBI Flexicap Fund?",
        "label_hi": "SBI Flexicap Fund का expense ratio / TER कहाँ मिलेगा?",
    },
)

I18N = {
    "en": {
        "tagline": (
            "This bot answers **factual** questions on **five SBI schemes** from "
            "public INDmoney + SBI/SEBI/AMFI documents."
        ),
        "disclaimer": "Facts-only. No investment advice.",
        "try_example": "Try an example:",
        "chat_placeholder": "Ask a factual question about an SBI scheme…",
        "history_title": "Chat History",
        "history_hint": "Questions you asked in this session.",
        "new_chat": "New Chat",
        "no_chats": "No chats yet. Ask a question below to start.",
        "questions_asked": "{n} question(s) asked",
        "last_asked": "Last asked",
        "at_utc": "at {ts} UTC",
        "empty_prompt": "Could you ask a factual question about one of the five SBI schemes? Here are some examples:",
        "no_coverage": (
            "I don't have that in this corpus. I only answer factual questions about "
            "the five SBI schemes from the public INDmoney + SBI/SEBI/AMFI documents."
        ),
        "error": "Sorry, I hit a retrieval error: {exc}. Please try again.",
        "citation": "Citation: [{url}]({url})",
        "evidence_title": "Retrieved evidence (Phase 5)",
        "evidence_ambiguous": "The question did not name a clear single scheme — showing general matches.",
        "evidence_e11": "E11 FAILURE: citation outside the §9 allowlist",
        "weaker_match": " (weaker match)",
        "increase_text": "Increase text size",
        "decrease_text": "Decrease text size",
        "theme_tooltip": "Switch to dark / light mode",
        "lang_tooltip_en": "Switch language to हिन्दी",
        "lang_tooltip_hi": "Switch language to English",
    },
    "hi": {
        "tagline": (
            "यह बॉट **पाँच SBI योजनाओं** के बारे में सार्वजनिक "
            "INDmoney + SBI/SEBI/AMFI दस्तावेज़ों से **तथ्यात्मक** प्रश्नों का उत्तर देता है।"
        ),
        "disclaimer": "केवल तथ्य। कोई निवेश सलाह नहीं।",
        "try_example": "एक उदाहरण आज़माएँ:",
        "chat_placeholder": "SBI योजना के बारे में तथ्यात्मक प्रश्न पूछें…",
        "history_title": "चैट इतिहास",
        "history_hint": "इस सत्र में पूछे गए प्रश्न",
        "new_chat": "नया चैट",
        "no_chats": "अभी तक कोई चैट नहीं है। शुरू करने के लिए नीचे प्रश्न पूछें।",
        "questions_asked": "{n} प्रश्न पूछे गए",
        "last_asked": "अंतिम प्रश्न",
        "at_utc": "{ts} UTC पर",
        "empty_prompt": "क्या आप पाँच SBI योजनाओं में से किसी एक के बारे में तथ्यात्मक प्रश्न पूछ सकते हैं? कुछ उदाहरण:",
        "no_coverage": (
            "यह मेरे डेटा-स्रोतों में नहीं है। मैं केवल सार्वजनिक INDmoney + SBI/SEBI/AMFI "
            "दस्तावेज़ों से पाँच SBI योजनाओं के बारे में तथ्यात्मक प्रश्नों का उत्तर देता हूँ।"
        ),
        "error": "क्षमा करें, पुनर्प्राप्ति में त्रुटि हुई: {exc}। कृपया पुनः प्रयास करें।",
        "citation": "स्रोत: [{url}]({url})",
        "evidence_title": "चरण 5: पुनर्प्राप्त साक्ष्य — उत्तर अंग्रेज़ी में हैं",
        "evidence_ambiguous": "प्रश्न में कोई एक स्पष्ट योजना नहीं थी — सामान्य मिलान दिखाए जा रहे हैं।",
        "evidence_e11": "E11 विफलता: §9 अनुमत सूची के बाहर उद्धरण",
        "weaker_match": " (कमज़ोर मिलान)",
        "increase_text": "पाठ बड़ा करें",
        "decrease_text": "पाठ छोटा करें",
        "theme_tooltip": "डार्क / लाइट मोड बदलें",
        "lang_tooltip_en": "भाषा हिन्दी करें",
        "lang_tooltip_hi": "Language switch to English",
    },
}

FONT_SCALE_MIN = 0.8
FONT_SCALE_MAX = 1.5
FONT_SCALE_STEP = 0.1


def _lang() -> str:
    return st.session_state.get("lang", "en")


def _txt(key: str, **kw: object) -> str:
    text = I18N[_lang()].get(key) or key
    return text.format(**kw)


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
            st.caption(_txt("citation", url=citation))


def _inject_style(font_scale: float) -> None:
    """App styling. Theme colors are delegated to Streamlit's native light/dark
    selection (Settings menu, top-right corner), so this CSS stays theme-agnostic."""
    fs = 16 * font_scale

    st.markdown(
        f"""<style>
        .stApp {{ font-size: {fs:.1f}px; }}

        /* Brand header: "SBI Mutual Funds" text, then logo, then accent "Chat-bot" */
        .brand-header {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            margin: 0;
            padding: 0;
            line-height: 1.15;
        }}
        .brand-header-lg {{ font-size: {fs * 1.65:.1f}px; }}
        .brand-header-sm {{ font-size: {fs * 1.2:.1f}px; }}
        .brand-header .accent {{ color: #7c3aed; }}
        .brand-header img {{
            height: 40px;
            width: auto;
            object-fit: contain;
            border-radius: 8px;
            background: white;
            padding: 2px;
        }}

        /* Chat input: darker field with a visible accent border */
        [data-testid="stChatInput"] {{
            background: #1f2430;
            border: 2px solid #7c3aed;
            border-radius: 12px;
        }}
        [data-testid="stChatInput"]:focus-within {{ border-color: #a78bfa; }}
        [data-testid="stChatInput"] textarea {{
            background: transparent;
            color: #fafafa;
            font-size: {fs:.1f}px;
        }}

        .stChatMessage {{ font-size: {fs:.1f}px; }}
        .tb-btn {{
            border: 1px solid rgba(128, 128, 128, 0.55);
            border-radius: 8px;
            padding: 0.15rem 0.6rem;
            font-size: {fs * 0.95:.1f}px;
            background: transparent;
            color: inherit;
        }}
        </style>""",
        unsafe_allow_html=True,
    )


def _brand_html(size: str) -> str:
    """Brand header: "SBI Mutual Funds" text first, then the logo, then accent
    "Chat-bot". Logo is inlined as base64 so it works regardless of asset serving."""
    parts = ["<span>SBI Mutual Funds</span>"]
    if _HAS_LOGO:
        import base64

        b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()
        parts.append(
            f"<img src='data:image/png;base64,{b64}' alt='SBI Mutual Funds logo'/>"
        )
    parts.append("<span class='accent'>Chat-bot</span>")
    return f'<div class="brand-header {size}">{"".join(parts)}</div>'


def _render_toolbar() -> None:
    """A-/A+ text size and language controls above the header. Dark/light theme is
    switched from the Streamlit corner menu: top-right ⮫ / Settings -> Theme."""
    fs = st.session_state.get("font_scale", 1.0)
    lang = _lang()

    c1, c2, c3, _spacer = st.columns([1, 1, 1, 6])

    with c1:
        if st.button("A−", key="tb_font_minus", help=_txt("decrease_text")):
            st.session_state.font_scale = round(
                max(FONT_SCALE_MIN, fs - FONT_SCALE_STEP), 2
            )
            st.rerun()
    with c2:
        if st.button("A+", key="tb_font_plus", help=_txt("increase_text")):
            st.session_state.font_scale = round(
                min(FONT_SCALE_MAX, fs + FONT_SCALE_STEP), 2
            )
            st.rerun()
    with c3:
        target = "हिं" if lang == "en" else "EN"
        tip_key = "lang_tooltip_en" if lang == "en" else "lang_tooltip_hi"
        if st.button(target, key="tb_lang", help=_txt(tip_key)):
            st.session_state.lang = "hi" if lang == "en" else "en"
            st.rerun()


def _short(text: str, limit: int = 60) -> str:
    text = " ".join(text.strip().split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _handle_question(question: str) -> None:
    question = question.strip()
    if not question:
        msg_text = _txt("empty_prompt")
        _render_chat("assistant", msg_text)
        st.session_state.messages.append({"role": "assistant", "content": msg_text})
        return

    _render_chat("user", question)
    st.session_state.messages.append(
        {"role": "user", "content": question, "asked_at": _utc_iso_now()}
    )

    try:
        result = _export_answer(question)
    except Exception as exc:  # noqa: BLE001
        msg_text = _txt("error", exc=exc.__class__.__name__)
        _render_chat("assistant", msg_text)
        st.session_state.messages.append({"role": "assistant", "content": msg_text})
        return

    # 6.2: no coverage -> refuse rather than guess
    if result["coverage"] == "no_coverage" or not result["chunks"]:
        body = _txt("no_coverage")
        cite = _citation(result)
        _render_chat("assistant", body, citation=cite)
        st.session_state.messages.append(
            {"role": "assistant", "content": body, "citation": cite}
        )
        return

    # 6.2 / 6.3: answer from the best retrieved passage, one citation, transparency
    top = result["chunks"][0]
    answer = _clip_answer(top["text"])
    weeks = _txt("weaker_match") if result["coverage"] == "weak" else ""
    body = f"{answer}{weeks}"
    st.markdown(f"_{_txt('disclaimer')}_")
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
    with st.expander(_txt("evidence_title")):
        if result.get("ambiguous"):
            st.warning(_txt("evidence_ambiguous"))
        if result.get("url_not_in_allowlist"):
            st.error(_txt("evidence_e11"))
        for i, c in enumerate(result["chunks"], start=1):
            st.markdown(
                f"**[{i}]** {c['scheme']} / {c['doc_type']} — distance {c['distance']}"
            )
            st.markdown(f"Source: [{c['url']}]({c['url']})")
            st.write(c["text"])


def _render_sidebar() -> None:
    """Left-hand drawer with chat history and quick actions."""
    lang = _lang()
    with st.sidebar:
        st.markdown(_brand_html("brand-header-sm"), unsafe_allow_html=True)
        st.markdown(f"### {_txt('history_title')}")
        st.caption(_txt("history_hint"))

        if st.button(f"➕ {_txt('new_chat')}", use_container_width=True, type="primary"):
            st.session_state.messages = []
            st.rerun()

        st.divider()

        user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
        if not user_msgs:
            st.info(_txt("no_chats"))
        else:
            st.caption(_txt("questions_asked", n=len(user_msgs)))
            for idx, m in enumerate(reversed(user_msgs), start=1):
                if st.button(
                    f"{idx}. {_short(m['content'])}",
                    key=f"hist_{idx}",
                    use_container_width=True,
                ):
                    st.session_state.pending = m["content"]
                    st.rerun()

        st.divider()

        if user_msgs:
            last = user_msgs[-1]
            st.markdown(f"**{_txt('last_asked')}**")
            st.write(_short(last["content"], limit=120))
            asked_at = last.get("asked_at", "")
            if asked_at:
                st.caption(_txt("at_utc", ts=asked_at[:19].replace("T", " ")))

        st.caption(
            f"{_txt('disclaimer')}  ·  {'EN' if lang == 'en' else 'हिं'}"
        )


def main() -> None:
    st.set_page_config(page_title=BRAND, page_icon="💰", layout="centered")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    if "font_scale" not in st.session_state:
        st.session_state.font_scale = 1.0

    _inject_style(st.session_state.font_scale)

    # Controls on top of the header: text size + language. Theme is switched from
    # the Streamlit corner menu (top-right ⮫ -> Settings -> Theme).
    _render_toolbar()

    st.markdown(_brand_html("brand-header-lg"), unsafe_allow_html=True)
    st.markdown(_txt("tagline"))
    st.caption(f"**{_txt('disclaimer')}**")

    # Clickable examples
    st.markdown(f"**{_txt('try_example')}**")
    cols = st.columns(len(EXAMPLES))
    for col, sample in zip(cols, EXAMPLES):
        label = sample["label_hi"] if _lang() == "hi" else sample["label_en"]
        if col.button(label, use_container_width=True):
            st.session_state.pending = sample["q"]

    # Render history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("citation"):
                st.caption(_txt("citation", url=msg["citation"]))
            if msg.get("last_updated"):
                st.caption(msg["last_updated"])

    pending = st.session_state.pop("pending", None)
    if pending:
        _handle_question(pending)

    prompt = st.chat_input(_txt("chat_placeholder"))
    if prompt:
        _handle_question(prompt)

    # Drawer last so it always reflects the latest session state.
    _render_sidebar()


if __name__ == "__main__":
    main()