@echo off
echo Starting AnnaSetu FastAPI Backend on http://localhost:8000 ...
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
