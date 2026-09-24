@echo off
echo Starting AnnaSetu Full Stack (FastAPI Backend + Next.js Frontend)...
start "AnnaSetu Backend (FastAPI)" cmd /k "cd backend && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
start "AnnaSetu Frontend (Next.js)" cmd /k "cd anna-setu-frontend-development && pnpm dev --port 3000"
echo.
echo ========================================================
echo  AnnaSetu is launching!
echo  - Frontend: http://localhost:3000
echo  - Backend:  http://localhost:8000
echo  - Swagger:  http://localhost:8000/docs
echo ========================================================
