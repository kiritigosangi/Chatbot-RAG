"""Launch the Streamlit UI from Chatbot/: python run_ui.py"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_PATH = ROOT / "code" / "ui" / "app.py"

import subprocess

def main() -> int:
    python = sys.executable
    return subprocess.call([python, "-m", "streamlit", "run", str(APP_PATH)])

if __name__ == "__main__":
    raise SystemExit(main())
