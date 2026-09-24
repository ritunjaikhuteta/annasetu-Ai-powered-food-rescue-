# AnnaSetu — Frontend Architecture & Supabase Auth (Phase 10)

> 🔗 **Live URL:** [https://annasetu-ai-powered-food-rescue-d2a.vercel.app](https://annasetu-ai-powered-food-rescue-d2a.vercel.app)

AnnaSetu is a verified, need-driven food rescue and logistics marketplace operating with three public roles:
- **DONOR**: Restaurants, caterers, hotels, supermarkets, corporate cafeterias, and approved food vendors.
- **RECEIVER**: Verified NGOs and charitable organizations that raise food needs and receive surplus food.
- **DELIVERY PARTNER (DRIVER)**: Verified logistics partners who transport food using appropriate vehicles.

---

## 1. Environment Variable Configuration

1. Copy `.env.example` to `.env.local`:
   ```bash
   cp .env.example .env.local
   ```
2. Populate the environment variables with your Supabase project keys:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://<your-project-ref>.supabase.co
   NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=eyJhbGciOi...
   ```
   > **Security Note**: Never expose the Supabase service role / secret key in client environment variables or repository code. Only public credentials (`NEXT_PUBLIC_*`) are used in client/SSR contexts.

---

## 2. Running the Application

Ensure Node.js (v18+) and `pnpm` are installed:

```bash
# Install dependencies
pnpm install

# Start the development server
pnpm dev --port 3000

# Build for production
pnpm build

# Start production server
pnpm start
```

---

## 3. Supabase Client Architecture & Email Confirmation

### Architecture
- **Browser Client** (`lib/supabase/client.ts`): Uses `@supabase/ssr` `createBrowserClient` with standard cookies.
- **Server Client** (`lib/supabase/server.ts`): Uses `@supabase/ssr` `createServerClient` bound to Next.js `cookies()` for SSR and server actions.
- **Session Middleware / Proxy** (`lib/supabase/proxy.ts`, `middleware.ts`): Automatically updates session tokens on non-static requests, prevents stale cookies, and enforces authenticated route boundaries.
- **Auth Provider & Hooks** (`lib/auth/context.tsx`): Reusable client hook `useAuth()` providing `user`, `profile`, `role`, `verificationStatus`, `isVerified`, `signIn`, `signUp`, and `signOut`.
- **Server Auth Helpers** (`lib/auth/server.ts`): `getCurrentUser`, `getCurrentProfile`, `requireUser`, `requireRole` for server-side guard execution.

### Email Confirmation Flow
1. User selects public role (`DONOR`, `RECEIVER`, or `DELIVERY PARTNER` / `DRIVER`) and registers via multi-step onboarding at `/auth`.
2. Form submits to `supabase.auth.signUp()` with metadata `{ full_name, role }`.
3. If email confirmation is enabled on Supabase, `signUp()` returns a user object without an active session (`session: null`).
4. The UI transitions to the **"Check your email"** confirmation screen with clear instructions.
5. The confirmation link points to `/auth/callback?code=...`.
6. `/auth/callback` handles the PKCE code exchange via `supabase.auth.exchangeCodeForSession(code)`, reads the user's role from `public.profiles`, and redirects the user directly to their respective portal (`/donor/dashboard`, `/receiver/dashboard`, or `/driver/dashboard`).

---

## 4. Role Routing & Authorizations

AnnaSetu relies strictly on the database table `public.profiles` (`profile.role`) as the authoritative source of truth. User metadata is never used for access authorization.

- **Role Selection**: Limited strictly to `DONOR`, `RECEIVER`, and `DRIVER`. `ADMIN` is strictly forbidden from public registration.
- **Route Protections**:
  - `/donor/*` requires authenticated session with `profile.role === 'DONOR'`.
  - `/receiver/*` requires authenticated session with `profile.role === 'RECEIVER'`.
  - `/driver/*` requires authenticated session with `profile.role === 'DRIVER'`.
  - `/admin/*` requires authenticated session with `profile.role === 'ADMIN'`.
- **Role Mismatch Handling**: If a user attempts to access a portal that does not match their assigned database role, they are redirected safely or signed out with an authorization notice.

---

## 5. Verification Gating

Upon signup, database triggers initialize `public.profiles`, and the application populates the corresponding role-specific profile (`donor_profiles`, `receiver_profiles`, or `driver_profiles`).

- Initial verification status is strictly `PENDING`.
- Unverified users (`PENDING`, `UNDER_REVIEW`, `REJECTED`) are gated from live operational actions:
  - **DONOR**: Can view portal, update organization profile, upload certificates, and prepare drafts, but **cannot publish active food donations**.
  - **RECEIVER**: Can view needs, browse listings, and manage NGO profile, but **cannot confirm operational handoffs / claim rescue food**.
  - **DRIVER**: Can view dashboard, route history, and earnings, but **cannot accept active rescue missions**.
- Status updates to `VERIFIED` can only be performed by platform administrators through secure operational workflows.

---

## 6. Phase 19 — Demo Mode & Environment Banner

To enable the subtle demo-environment banner (amber at top of every page) and
activate canonical mock data fallbacks for the seeded scenario, set in your
shell or `.env.local`:

```env
# Enable the demo banner and mock-data fallbacks for the hackathon scenario
NEXT_PUBLIC_DEMO_MODE=true

# Optional informational label (development / staging)
NEXT_PUBLIC_APP_ENV=development
```

Safety: When `NEXT_PUBLIC_DEMO_MODE` is unset or `false` (default), no
demo banner appears and the UI behaves as a production portal.

### Canonical Seeded Scenario Identities (Phase 19)

All role portals and all mock data reference the same scenario — names,
IDs, quantities, seal IDs, and OTP values are deliberately consistent
across donor, receiver, driver, admin, and landing pages:

| Entity       | Identity                                  |
|--------------|-------------------------------------------|
| **Donor**    | Green Leaf Catering (Sector 17, Gurugram, HR) |
| **Receivers** (allocations) | Seva Community Kitchen (12 kg), Anna Sadan Charitable Trust (8 kg), Sahara Community Home (20 kg) — Total 40 kg |
| **Driver**   | Arjun Sharma · Insulated Van · DL 12 CA 4455 |
| **Donation** | AS-GL-0001 · 40 kg Vegetarian Cooked Meals · 20 kg remaining |
| **Delivery** | demo_del_001 — Stop 1 COMPLETED · Stop 2 IN_PROGRESS · Stops 3+4 PENDING |
| **Tamper Seal** | AS-GL-000047                           |
| **Pickup OTP** | 4729                                  |
| **Financials** | NGO wallet reservation ₹480 · Driver payout ₹264 · Platform fee ₹96 |
| **Exception** | 1 delivery status `REASSIGNMENT_REQUIRED` (mechanical breakdown) shown on Admin operations console |
| **Integrity** | 1 check status `REVIEW_REQUIRED` with admin note on Admin integrity queue |

The same identities and IDs are used on the backend seed service
(`backend/app/services/demo_service.py`) so both backend API responses
and frontend mock state are byte-level consistent.

---

## 7. Phase 19 — AI Positioning (Language Constraints)

The frontend uses conservative and accurate language about AI:

> **AI assists with document understanding, image review, natural-language
> explanations, and draft copy generation.**
> **Deterministic backend algorithms control eligibility, matching,
> allocation, routing, pricing, payment settlement, delivery state,
> verification status, role authorization, and wallet accounting.**

Components with AI copy (do not overclaim):

- `DonorApp → FoodIntegrity` panel: "No visible package discrepancy detected.
  This visual check supports review and does not prove food safety or
  guarantee no tampering."
- `DonorApp → NewDonation → Food Vision`: "Visual assistance", "Your
  declared quantity remains authoritative", "Possible information mismatch
  — please verify".
- `ReceiverApp → AIInsight`: Smart allocation notification uses
  "Optimal Match 96%" as a deterministic priority score (not an AI score).
- `NewDonation → creation-note`: "AI only assists with visual review and
  description. Your declared information stays authoritative."

---

## 8. Phase 19 — Centralized Status System

`components/rescue/RescueStatus.tsx` exports the deterministic `STATUS_TOKENS`
map (21 statuses including `reassignment_required`, `review_required`,
`under_review`, `in_progress`) used by Donor / Receiver / Driver / Admin
portals. Never invent one-off status colors in individual components —
use `<RescueStatus status="…">` so color, icon-dot, and `role="status"`
accessibility labeling remain consistent.

Launch commands for the demo run:

```bash
# Terminal 1 — Backend:
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend (with demo banner):
cd anna-setu-frontend-development
NEXT_PUBLIC_DEMO_MODE=true pnpm dev --port 3000

# (Optional — before demo) Reset & reseed canonical scenario:
cd backend
python scripts/seed_demo.py --reset
```

For the full timed 04:00 narrative, see `docs/HACKATHON_DEMO.md`.
