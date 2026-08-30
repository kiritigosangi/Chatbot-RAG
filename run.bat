@echo off
cd /d "%~dp0code"
set PYTHONPATH=%~dp0code
"%~dp0.venv\Scripts\python.exe" -m streamlit run ui/app.py --server.port 8501 --server.headless true
pause
