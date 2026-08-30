"""Run from Chatbot/: python run_phase3.py"""

from __future__ import annotations

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent / "code"
sys.path.insert(0, str(CODE_DIR))

from embedding.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
