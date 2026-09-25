# AnnaSetu — AI-Powered Food Rescue Network

[![Live App](https://img.shields.io/badge/Live%20Demo-Vercel-success?style=for-the-badge&logo=vercel)](https://annasetu-ai-powered-food-rescue-d2a.vercel.app)

> 🔗 **Live URL:** [https://annasetu-ai-powered-food-rescue-d2a.vercel.app](https://annasetu-ai-powered-food-rescue-d2a.vercel.app)

AnnaSetu connects surplus food from restaurants, caterers, and events with communities, shelters, and NGOs that need it most. A verified logistics and rescue platform powered by deterministic matching, multimodal AI verification, and secure GPS/OTP handoffs.

---

## 🏗️ Architecture

The repository contains both frontend and backend services:

```
annasetu/
├── anna-setu-frontend-development/    # Next.js 16 (Turbopack, TailwindCSS, TypeScript)
├── backend/                           # FastAPI backend (Deterministic matching, Supabase, AI services)
├── docs/                              # Project documentation & demo walk-throughs
├── run_all.bat                        # Starts both frontend and backend concurrently
├── run_backend.bat                    # Starts the FastAPI backend
└── run_frontend.bat                   # Starts the Next.js frontend
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js (v18+) and pnpm / npm
- Python (3.10+)

### Running Locally

To run both services together:
```bash
./run_all.bat
```

Or run them individually:

#### 1. Backend (FastAPI)
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

#### 2. Frontend (Next.js)
```bash
cd anna-setu-frontend-development
npm install # or pnpm install
npm run dev
```
- Application: `http://localhost:3000`

---

## 🌟 Key Features

- **Role-Based Workspaces**: Specialized portals for Donors, Receivers (NGOs/Shelters), Delivery Partners, and Admins.
- **AI-Powered Visual Food Quality Assessment (Google Gemini)**: Multimodal visual inspection of surplus food photos during donation creation using the official `google-genai` SDK. Outputs structured Visual Quality Scores (0-100), freshness signals, packaging conditions, and manual review recommendations while keeping deterministic backend business logic strictly authoritative.
- **AI Matching & Verification**: Multimodal image verification for food integrity and priority scoring algorithms.
- **Verified Handoffs**: Chain-of-custody verification via OTP confirmation and GPS checkpoint logging.
- **Real-time Operations**: Live rescue tracking and status transitions across the journey from kitchen to meal.

---

## 🌐 Vercel Deployment (Frontend)

When deploying this monorepo to Vercel:

1. In the Vercel Dashboard, go to **Settings** > **General**.
2. Under **Root Directory**, click **Edit** and set it to:
   ```text
   anna-setu-frontend-development
   ```
3. Click **Save**.
4. Trigger a new deployment or click **Redeploy**. Vercel will automatically detect `Next.js 16`, install dependencies, and build the application cleanly.
