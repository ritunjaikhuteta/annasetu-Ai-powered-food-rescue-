# AnnaSetu — FastAPI Backend Foundation & Core Rescue Engine (Phase 11 & 12)

Production-grade FastAPI backend foundation and deterministic rescue engine for the AnnaSetu verified food rescue & logistics platform.

---

## 1. Architecture Overview

```
backend/
├── app/
│   ├── main.py                  # FastAPI application entrypoint, middleware & routing
│   ├── core/
│   │   ├── config.py            # Pydantic BaseSettings & environment configs
│   │   ├── security.py          # Supabase JWT token verification
│   │   └── dependencies.py      # Auth, profile, role, & verification dependencies
│   ├── db/
│   │   └── supabase.py          # Centralized server-side Supabase REST/Auth client with CAS locking
│   ├── models/                  # Domain model mapping
│   ├── schemas/
│   │   ├── common.py            # UserRole & VerificationStatus enums, Health models
│   │   ├── auth.py              # AuthenticatedUser, MeResponse, ProfileUpdate models
│   │   ├── user.py              # User summary response models
│   │   ├── donor.py             # DonorProfileResponse & safe DonorProfileUpdate
│   │   ├── receiver.py          # ReceiverProfileResponse & safe ReceiverProfileUpdate
│   │   ├── driver.py            # DriverProfileResponse & safe DriverProfileUpdate
│   │   ├── need.py              # NeedCreate, NeedResponse, NeedUpdate, MealPeriod, NeedStatus
│   │   ├── donation.py          # DonationCreate, DonationResponse, DonationUpdate, StorageCondition
│   │   ├── match.py             # MatchResponse, PriorityBreakdown, PriorityLabel
│   │   └── allocation.py        # AllocationCreate, AllocationResponse, AllocationStatus
│   ├── api/
│   │   ├── deps.py              # Route dependency & service injections
│   │   └── routes/
│   │       ├── health.py        # /health, /api/v1/health, /api/v1/info
│   │       ├── users.py         # /api/v1/me (Identity & authoritative profile)
│   │       ├── profiles.py      # /api/v1/me/profile (Self-service profile)
│   │       ├── donor.py         # /api/v1/donor/profile
│   │       ├── receiver.py      # /api/v1/receiver/profile
│   │       ├── driver.py        # /api/v1/driver/profile
│   │       ├── needs.py         # /api/v1/needs CRUD & activation/cancellation
│   │       ├── donations.py     # /api/v1/donations CRUD & posting/cancellation
│   │       ├── matches.py       # /api/v1/donations/{id}/generate-matches & match queries
│   │       └── allocations.py   # /api/v1/allocations (Transactional allocation)
│   ├── services/
│   │   ├── auth_service.py      # Authoritative profile lookup & verification check
│   │   ├── profile_service.py   # Profile read & safe updates
│   │   ├── donor_service.py     # Donor profile management
│   │   ├── receiver_service.py  # Receiver NGO profile management
│   │   ├── driver_service.py    # Driver operational profile & availability
│   │   ├── routing_provider.py  # RoutingProvider abstraction (Haversine & ETA)
│   │   ├── need_service.py      # NGO Need creation, activation & quantity invariants
│   │   ├── donation_service.py  # Surplus Donation publishing (min 5kg) & lifecycle
│   │   ├── matching_service.py  # Deterministic matching & rescue priority engine
│   │   ├── allocation_service.py# Atomic allocations, CAS locking & race condition prevention
│   │   ├── notification_service.py # Deterministic notification delivery
│   │   └── audit_service.py     # Tamper-evident mutation audit logging
│   └── utils/
│       ├── exceptions.py        # Centralized exception hierarchy (401, 403, 404, 409, 422, 500)
│       └── responses.py         # Standardized ErrorResponse & SuccessResponse wrappers
├── tests/
│   ├── conftest.py              # MockSupabaseClient & TestClient fixtures
│   ├── test_health.py           # Health & service info tests
│   ├── test_auth.py             # Auth verification & /api/v1/me tests
│   ├── test_roles.py            # Role checking & cross-role access barrier tests
│   ├── test_profiles.py         # Profile retrieval, safe updates, & validation tests
│   ├── test_needs.py            # NGO Need lifecycle & quantity validation tests
│   ├── test_donations.py        # Surplus donation rules, 5kg min, & timeline tests
│   ├── test_matching.py         # Deterministic matching, diet filters & score tests
│   └── test_allocations.py      # Multi-split allocation & concurrency safety tests
├── requirements.txt             # Minimal dependencies
├── .env.example                 # Environment template
└── README.md
```

---

## 2. Core Rescue Workflow (Phase 12)

```
RECEIVER CREATES NEED (/api/v1/needs)
        ↓
RECEIVER ACTIVATES NEED (/api/v1/needs/{id}/activate)
        ↓
DONOR POSTS SURPLUS DONATION (/api/v1/donations -> /post)
        ↓
SYSTEM CHECKS HARD ELIGIBILITY (Diet, Category, Window, Timeline, Capacity)
        ↓
SYSTEM CALCULATES DETERMINISTIC RESCUE PRIORITY (0–100)
        ↓
MATCH IS PERSISTED (/api/v1/donations/{id}/generate-matches)
        ↓
TRANSACTIONAL CAS ALLOCATION (/api/v1/allocations)
        ↓
RECEIVER IS NOTIFIED (notifications table) & AUDITED (audit_logs)
```

### Deterministic Matching Algorithm
The matching engine evaluates 11 hard eligibility criteria without AI:
1. Donation is `POSTED` or active.
2. Need is `ACTIVE` or `PARTIALLY_FULFILLED`.
3. Food diet compatibility (`VEGETARIAN` fulfills `VEGETARIAN`/`MIXED`, `NON_VEGETARIAN` fulfills `NON_VEGETARIAN`/`MIXED`).
4. Food category matches.
5. Need has `remaining_quantity_kg > 0`.
6. Need physical receiving capacity >= minimum allocatable quantity.
7. Available before rescue deadline.
8. Receiving window compatible.
9. Estimated arrival before donation deadline and need `required_by`.
10. Valid coordinates for pickup and delivery.
11. Donation remaining quantity >= need minimum batch quantity.

### Priority Score Formula
```python
priority_score = (
    expiry_score * 0.30
    + eta_score * 0.25
    + distance_score * 0.20
    + fulfillment_score * 0.15
    + route_score * 0.10
)
```
Clamped to `[0, 100]` and classified into operational labels:
- `HIGH`: >= 75
- `MEDIUM`: 50–74
- `LOW`: < 50

### Concurrency & Over-Allocation Protection
- **In-process Mutex**: `asyncio.Lock` keyed per `donation_id` serializes simultaneous requests targeting the same donation.
- **Compare-And-Swap (CAS)**: Optimistic locking on `donations.remaining_quantity_kg` and `ngo_needs.remaining_quantity_kg` prevents double allocations. If another worker commits an update concurrently, the operation is rolled back and rejected with HTTP 409 (`ConflictException`).

---

## 3. Phase 13 & 14 Logistics & Verification

### Delivery Missions & Driver Operations (Phase 13)
- Multi-stop mission sequencing (pickup + up to 3 delivery stops).
- Deterministic route feasibility checking (deadline adherence).
- Driver discovery, capacity filtering, and deterministic ranking.
- Atomic offer acceptance using CAS lock with single-winner guarantee.
- State machine progression: `OPEN` -> `ACCEPTED` -> `ARRIVING_PICKUP` -> `PICKED_UP` -> `IN_TRANSIT` -> `AT_STOP` -> `DELIVERED`.

### Trust & Handoff Verification (Phase 14)
- **Secure OTP Service**: Short numeric OTP generated with cryptographic randomness; stored as salted SHA-256 HMAC hash; single-use with configurable expiry (10 min) and attempt limits (5 max); verified in constant time (`hmac.compare_digest`).
- **GPS Proximity Validation**: Haversine distance verification ensures driver is physically within the configurable radius (300m) of pickup and delivery coordinates before handoff verification can succeed.
- **Tamper-Evident Seals**: Random non-sequential IDs (`ANNA-<random-id>`) applied at pickup (`INTACT`); condition inspected and recorded at delivery stop (`INTACT`, `BROKEN`, `MISSING`, `DISPUTED`).
- **Private Evidence Storage**: Package and seal photo uploads stored under access-controlled bucket paths (`handoff-evidence/deliveries/{id}/...`).
- **Visual Integrity Check & AI Fallback**: Automated visual packaging comparison between pickup and delivery images; Groq vision model integration with non-blocking fallback if unavailable; neutral operational language ("No visible package discrepancy detected", "Possible package discrepancy — manual review required").
- **Manual Operational Review**: Admin API endpoints to list and resolve discrepancies (`CLEARED`, `REQUIRES_ACTION`, `DISPUTED`).

### Payments, Wallet, & Subscriptions (Phase 15)
- **Deterministic Pricing**: Decimal-safe monetary arithmetic (`Decimal.quantize(0.01)`). Formula: `delivery_charge = base_fare + (distance_km * per_km) + (duration_mins * per_min) + (stops * stop_fee)`.
- **Configurable Platform Fee**: 12% service fee (`platform_fee = delivery_charge * 0.12`). Total NGO payment = `delivery_charge + platform_fee`.
- **Driver Payout**: Calculated server-side as `max(minimum_payout, delivery_charge * payout_multiplier)`.
- **Price Snapshot**: Delivery pricing is snapshotted onto the delivery record upon reservation so historical rates are never recalculated.
- **Digital Wallet & Ledger**: NGO and Driver wallets with atomic available balance calculation (`balance - reserved_balance`), top-ups, and immutable auditable transaction ledger entries.
- **Atomic Fund Reservations**: Funds are held prior to delivery commitment; insufficient funds reject reservation with HTTP 409 (`INSUFFICIENT_FUNDS`).
- **Final Settlement**: Triggered only upon verified `DELIVERED` status; captures NGO payment, records 12% platform fee, credits driver payout, and marks delivery settled.
- **Payment Provider Abstraction**: Isolated `PaymentProvider` interface with `MockPaymentProvider` (instant simulated demo payments) and `RazorpayPaymentProvider` (cryptographic HMAC-SHA256 signature verification).
- **Donor Subscriptions & Entitlements**: Subscription tiers (`Starter`, `Business`, `Enterprise`) with server-side pricing, monthly/yearly billing cycles, and feature entitlements.
- **Administrative Refunds**: Full or partial refunds up to captured delivery charge.

### AI Assistance, OCR & Document Intelligence (Phase 16)
- **AI Provider Abstraction (`backend/app/ai/`)**: Fully isolated `AIProvider` base class with `GroqProvider` implementing `extract_document_data`, `normalize_food_description`, `generate_explanation`, and `analyze_package_integrity` (reusing Phase 14 `GroqVisionIntegrityAnalyzer`).
- **Authoritative Deterministic Safeguards**: AI is strictly an assistive layer. Deterministic backend logic remains 100% authoritative for eligibility, matching, allocation, routing, pricing, payment, delivery state, and verification status. AI never independently approves or rejects any person, organization, document, or handoff.
- **Graceful Fallbacks & Offline Resilience**: When `AI_ENABLED=false` or `GROQ_API_KEY` is missing/offline, all endpoints continue working seamlessly using deterministic regex parsers and templated operational explanations. Core food rescue operations are never blocked.
- **Deterministic OCR First**: Quantity (kg, grams), document numbers (GSTIN, PAN, FSSAI, RC plates), dates, and meal periods/diets are parsed deterministically before any AI call.
- **Verification Consistency Checks**: Compares candidate fields in `verification_documents.extracted_data` with authoritative `profiles`, `donor_profiles`, `receiver_profiles`, and `driver_profiles`. Outputs `MATCH`, `MISMATCH`, `PARTIAL_MATCH`, `NOT_CHECKED`, flagging expired documents and routing directly to `MANUAL_REVIEW`. Admin review remains the sole final authority.
- **Food Normalization & Invariant Preservation**: Free-text food descriptions extract candidate categories, diet types, and quantities. Crucially, the donor-declared quantity (`quantity_kg`) remains strictly authoritative; AI estimates serve only as a consistency signal.
- **Human-Readable Explanations**: Converts deterministic priority score breakdowns, delivery milestone updates, and recorded impact metrics into natural language without modifying any scores, factors, or numbers.
- **Privacy, Prompt Safety & Rate Limiting**: Prompts strictly prohibit inferring protected personal attributes (caste, religion, health, politics). No secrets, JWTs, or payment credentials are sent to AI providers. Sliding-window rate limiters prevent cost runaway.

### Admin & Operations Command Center (Phase 17)
- **Authoritative Server-Side Security**: Administrative actions are guarded strictly with `require_admin()` validating `profiles.role == ADMIN` via verified JWT tokens. Never trusts client headers or URL parameters.
- **Platform Operations Overview (`/api/v1/admin/overview`)**: High-density real-time metrics aggregated from database records (active entities, in-transit deliveries, pending reviews, exceptions, food rescued kg, and meal equivalents).
- **Service Operational Health**: Real-time health reporting for AI Provider (`AVAILABLE`/`DEGRADED`/`DISABLED`), Routing (`AVAILABLE`/`FALLBACK`), Payment Gateway (`AVAILABLE`/`MOCK`), and Database (`AVAILABLE`/`ERROR`).
- **Verification Review Queue (`/api/v1/admin/verifications`)**: Oldest-pending-first queue with document previews, candidate OCR extractions, and consistency check evidence. Controlled human approval/rejection explicitly updates profile status with auditable notes.
- **Live Rescue Operations & Logistics (`/api/v1/admin/operations/active`)**: Real-time transit monitoring with driver assignment, current stops, ETAs, and deterministic urgency classification (`NORMAL`, `ELEVATED`, `AT_RISK`).
- **Delivery Exceptions & Driver Reassignment (`/api/v1/admin/deliveries/{id}/reassign`)**: Deterministic reassignment workflow verifying target driver status, vehicle capacity, and schedule availability while preserving previous driver in audit logs.
- **Package Integrity Discrepancy Queue (`/api/v1/admin/integrity/reviews`)**: Side-by-side evidence review for seal status discrepancies (`CLEARED`, `REQUIRES_ACTION`, `DISPUTED`).
- **Financial Exceptions & Ledger Adjustments (`/api/v1/admin/financial/adjust`)**: Detection of settlement failures and stale reservations. Controlled creation of `ADJUSTMENT` transactions linking original references without modifying historical transactions in-place.
- **User & Driver Directory (`/api/v1/admin/users`)**: Searchable user directory with controlled activation/deactivation requiring documented administrative reasons.
- **Append-Only Audit Trail (`/api/v1/admin/audit-logs`)**: Paginated audit log retrieval with automatic redaction of sensitive credentials.
- **Multi-Period Rescue Analytics (`/api/v1/admin/analytics/`)**: Environmental impact, operational efficiency, and financial breakdown filtered by `today`, `7d`, `30d`, `90d`, or custom timeframes.

---

## 4. Running the Backend & Tests

```bash
# Navigate to backend directory
cd backend

# Run the full test suite (88 passing tests)
python -m pytest -v

# Start the development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive API documentation:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 5. Phase 19 — Demo Mode & Canonical Scenario Seed System

### 5.1 Configuration

Copy `.env.example` to `.env` and configure at minimum:

```env
# ── Runtime ──────────────────────────────────────────────
APP_ENV=development              # development | staging | production
PORT=8000

# ── Demo Mode (Triple-Gated Safety) ──────────────────────
# DEMO_MODE is AUTOMATICALLY DISABLED in APP_ENV=production
# regardless of this value (see settings.demo_enabled_safely).
DEMO_MODE=true
DEMO_NAMESPACE_TAG=DEMO_SCENARIO_1

# Optional 4th gate on reset endpoint (if set, client must send
# X-Demo-Reset-Token header on POST /api/v1/admin/demo/reset)
DEMO_RESET_TOKEN=DEMO_RESET_123456789

# ── Supabase ─────────────────────────────────────────────
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=ey...
SUPABASE_SERVICE_ROLE_KEY=ey...
SUPABASE_JWT_SECRET=<super-secret>

# ── Payments (optional, uses MockPaymentProvider if empty)
PAYMENT_PROVIDER=mock

# ── Routing (optional, uses Haversine fallback if empty)
ROUTING_PROVIDER=haversine

# ── AI (optional, uses deterministic fallback if disabled)
AI_ENABLED=false
```

### 5.2 Safety Guarantees

Demo mode is defended in depth:

1. **Production structural block**: `settings.demo_enabled_safely` returns
   `False` unconditionally if `APP_ENV=production` (even if DEMO_MODE=true
   is accidentally left in env).
2. **Endpoint gating**: `POST /seed` and `POST /reset` are guarded with
   `Depends(require_admin)` — only ADMIN-role JWT holders can call them.
   The public `GET /info` endpoint only returns metadata, never touches data.
3. **Namespace isolation (critical)**: Every demo-owned row on every table
   carries `demo_namespace_tag = DEMO_SCENARIO_1`. Reset deletes ONLY rows
   carrying this tag (24 tables, dependency-ordered cascade) — real user
   data is never touched.
4. **Confirm + token guard (reset)**: `POST /reset` requires query
   `confirm=true` AND optionally `X-Demo-Reset-Token: <value>` if
   `DEMO_RESET_TOKEN` is configured.

### 5.3 Demo Seed CLI (`scripts/seed_demo.py`)

```bash
cd backend

# (Recommended) Wipe existing demo rows + reseed canonical scenario:
python scripts/seed_demo.py --reset

# Only seed (assumes clean state):
python scripts/seed_demo.py

# Only reset (no reseed — clears the scenario):
python scripts/seed_demo.py --only-reset
```

CLI output includes a credentials table (5 roles), scenario IDs, and
a 20-step golden-flow checklist.

### 5.4 Admin Reset HTTP Endpoints

```
POST   /api/v1/admin/demo/seed                 (DEMO_MODE + ADMIN)
POST   /api/v1/admin/demo/reset?confirm=true   (DEMO_MODE + ADMIN + optional token)
GET    /api/v1/admin/demo/info                 (public)
```

### 5.5 Canonical Seeded Scenario (40 kg · Green Leaf)

| Entity        | Identity                               |
|---------------|----------------------------------------|
| **Donor**     | Green Leaf Catering (Sector 17, Gurugram) |
| **Receiver A** (12 kg) | Seva Community Kitchen (Sector 29, 20 kg lunch need, partially fulfilled) |
| **Receiver B** (8 kg)  | Anna Sadan Charitable Trust (Sector 12) |
| **Receiver C** (20 kg) | Sahara Community Home (Sector 46) |
| **Driver**    | Arjun Sharma · Insulated Van · DL 12 CA 4455 |
| **Donation**  | AS-GL-0001 · 40 kg Vegetarian Cooked Meals · 20 kg remaining |
| **Delivery**  | demo_del_001 · Stop 1 PICKUP done · Stop 2 IN_PROGRESS · Stops 3+4 PENDING |
| **Seal ID**   | AS-GL-000047                          |
| **Pickup OTP** | 4729                                 |
| **Wallet**    | NGO wallet reservation ₹480 · Driver payout ₹264 · Platform fee ₹96 |
| **Exception** | demo_del_exception_001 · `REASSIGNMENT_REQUIRED` (mechanical breakdown) |
| **Integrity** | 1 check status `REVIEW_REQUIRED` with admin review note |

---

## 6. Phase 19 — AI Positioning (Authoritative vs Assistive)

The project's AI language is deliberately conservative and accurate:

> **AI assists with document understanding, image review, natural-language
> explanations, and draft copy generation.**
> **Deterministic backend algorithms control eligibility, matching,
> allocation, routing, pricing, payment settlement, delivery state,
> verification status, role authorization, and wallet accounting.**

Specifics (do not weaken):

- Matching and priority scores: 100% deterministic formula with 6 weighted factors.
- Allocation and wallet reservations: 100% atomic CAS transactions.
- Donor-declared food quantity: 100% authoritative; AI quantity estimates serve only as a consistency signal.
- Verification approvals: Admin is always the final reviewer. AI flags candidates and expired documents.
- Food integrity image analysis: AI provides an assistive notice ("No visible package discrepancy detected") and is never a proof of food safety or guarantee of no tampering.
- When `AI_ENABLED=false` every endpoint still works using deterministic regex parsers and templated language. Core operations are never blocked on AI availability.

---

## 7. Phase 19 — Definition of Done

Checklist items are implemented:

1. ✅ `APP_ENV` + `DEMO_MODE` in backend settings with production auto-block
2. ✅ `NEXT_PUBLIC_DEMO_MODE` in frontend + subtle banner indicator
3. ✅ Demo seed service (65+ records across 24 tables)
4. ✅ Demo reset service (namespace-isolated, cascade ordered)
5. ✅ Admin demo seed + reset + info endpoints (gated)
6. ✅ `scripts/seed_demo.py` CLI with preflights
7. ✅ Canonical Green Leaf 40 kg scenario identities consistent across backend + frontend
8. ✅ 12 + 8 + 20 kg allocation, 20 kg donation remaining
9. ✅ Stop 2 IN_PROGRESS with driver next-action visible
10. ✅ Tamper seal ID AS-GL-000047 + OTP 4729 shared
11. ✅ Wallet reservation ₹480 / payout ₹264 / fee ₹96
12. ✅ 1 operational exception delivery + 1 integrity review example
13. ✅ Cross-role authorization: 88 backend tests (incl. 7 role-cross-access tests)
14. ✅ Deterministic status color system: STATUS_TOKENS map in RescueStatus component
15. ✅ Contextual Empty / Loading / Error states (shared components)
16. ✅ No frontend secrets (grep audit; .env in .gitignore; service_role keys only backend-side)
17. ✅ Database invariants: allocations ≤ donation/need, wallet balance ≥ 0 (enforced in CAS)
18. ✅ No Lorem ipsum / placeholder text in source (only in node_modules tests)
19. ✅ 88/88 backend pytest passing
20. ✅ Frontend production build passing
21. ✅ Recharts impact charts (AreaChart kg/month, BarChart meals/month)
22. ✅ Priority /100 with "Calculated from operational factors" language on UI
23. ✅ docs/HACKATHON_DEMO.md timed script (00:15 → 04:00)
24. ✅ Golden demo flow: 30 steps end-to-end in scenario data



