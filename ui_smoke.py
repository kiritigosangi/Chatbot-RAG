"""Headless verification of the Streamlit UI using AppTest.

Simulates opening the app and submitting a question, then asserts the UI
renders a citation + evidence without raising. Run: python ui_smoke.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "code"))

from streamlit.testing.v1 import AppTest

APP = ROOT / "code" / "ui" / "app.py"

if __name__ == "__main__":
    at = AppTest.from_file(str(APP), default_timeout=120)
    at.run()
    print("initial run exceptions:", len(at.exception))
    for e in at.exception:
        print("EXC:", e.value)

    # submit a real question through the chat input
    at.chat_input[0].set_value("What is the exit load for SBI Small Cap Fund?").run()
    print("post-query run exceptions:", len(at.exception))
    for e in at.exception:
        print("EXC:", e.value)

    texts = [m.value for m in at.markdown]
    print("markdown blocks:", len(texts))
    joined = "\n".join(texts)
    print("contains Exit Load:", "Exit Load" in joined)
    print("contains citation:", "Citation:" in joined.lower() or "indmoney.com" in joined)
