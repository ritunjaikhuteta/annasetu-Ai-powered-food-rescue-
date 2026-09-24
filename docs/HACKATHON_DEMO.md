# AnnaSetu — Hackathon Demo Script

Timed 3-minute 40-second walkthrough for the canonical Phase 19 scenario.
Practice run target: ≤ 4:00 end-to-end.

---

## Pre-flight (before demo starts — 00:00 → 00:15)

1. Backend running: `cd backend && python -m uvicorn app.main:app --reload --port 8000`
2. Frontend running: `cd anna-setu-frontend-development && NEXT_PUBLIC_DEMO_MODE=true pnpm dev --port 3000`
3. Seeded: `cd backend && python scripts/seed_demo.py --reset` (prints credentials table)
4. Browser tabs open:
   - **Tab 1 — Landing** http://localhost:3000/
   - **Tab 2 — Donor**   http://localhost:3000/donor/dashboard   (signed in as **Green Leaf Catering**)
   - **Tab 3 — Receiver** http://localhost:3000/receiver/dashboard (signed in as **Seva Community Kitchen**)
   - **Tab 4 — Driver**   http://localhost:3000/driver/dashboard   (signed in as **Arjun Sharma**)
   - **Tab 5 — Admin**    http://localhost:3000/admin/dashboard    (signed in as **Admin Priya**)

### Demo credentials (seeded scenario)

| Role     | Email (login)            | Password | Display name                     |
|----------|--------------------------|----------|----------------------------------|
| DONOR    | donor.greenleaf@annasetu.in  | Demo@12345 | Green Leaf Catering            |
| RECEIVER | recv.seva@annasetu.in        | Demo@12345 | Seva Community Kitchen         |
| RECEIVER | recv.annasadan@annasetu.in   | Demo@12345 | Anna Sadan Charitable Trust    |
| DRIVER   | driver.arjun@annasetu.in     | Demo@12345 | Arjun Sharma — DL 12 CA 4455   |
| ADMIN    | admin.priya@annasetu.in      | Demo@12345 | Admin Priya                    |

Canonical handoff IDs:
- Donation AS-GL-0001 · 40 kg vegetarian cooked meals
- Delivery demo_del_001 · stops: PICKUP_COMPLETE → STOP_2 IN_PROGRESS → STOP_3 PENDING → STOP_4 PENDING
- Tamper seal **AS-GL-000047** · Pickup OTP **4729** · Seva Kitchen handoff OTP **4729**
- Wallet reservation **₹480** · Driver payout **₹264** · Platform fee **₹96**

---

## Timed demo narrative (00:15 → 04:00)

### Segment 1 — Landing & trust narrative (00:15 → 00:45)

> "AnnaSetu connects surplus food from verified food businesses to verified receiving organizations — through verified delivery partners. Every handoff has a checkpoint."

1. **(00:15)** Tab 1 Landing → scroll to **Logistics example** section
2. Point to allocation card: *"One 40 kg donation from Green Leaf Catering in Gurugram → distributed as 12 kg → Seva Community Kitchen, 8 kg → Anna Sadan Trust, 20 kg → Sahara Community Home."*
3. Scroll to **Trust section**: *"Verified businesses · Verified NGOs · Verified drivers · GPS+OTP handoffs · Tamper-evident seals · AI-assisted food integrity check"*
4. **(00:40)** Click role → Donor → **Switch to Tab 2 (Donor)**

### Segment 2 — Donor: surplus to rescue (00:45 → 01:20)

> "Donor 'Green Leaf Catering' posted surplus at 2:30 PM today. Within minutes the network matched it to three nearby needs."

1. Dashboard greeting → **Active Rescue card**
2. Point to:
   - Route 9.1 km / ETA minutes (live)
   - Driver: **Arjun Sharma, Insulated Van DL 12 CA 4455** ✅ verified
   - **Rescue deadline** (prominent orange)
   - **Rescue Priority 92/100** → explain: *"Calculated from distance, ETA, quantity, receiver capacity, meal period, and remaining time window. Priority is deterministic — not a score from AI."*
3. Click **Track Rescue** → **Live Logistics view**
   - Route stops: **01 Green Leaf Catering** pickup verified → **02 Seva Community Kitchen** (current stop) → 03 Anna Sadan → 04 Sahara Home
   - Handoff evidence: **Seal ID AS-GL-000047** (show seal ID)
   - Food Integrity AI box: *"AI assists with understanding handoff images. The visual check supports review — it does not prove food safety or guarantee no tampering."*
4. **(01:18)** Switch to **Tab 3 (Receiver)**

### Segment 3 — Receiver: need to fulfillment (01:20 → 01:55)

> "Seva Community Kitchen raised a 20 kg lunch need this morning. The matching engine allocated 12 kg to them from this donation. Driver is now 11 minutes away."

1. Receiver dashboard → **AI Insight card**: *"Open lunch capacity automatically matched to surplus vegetarian meals from Green Leaf Catering (2.4 km away)."*
2. Metric tiles: **Open Capacity 40 / Active Needs 2 / Incoming Today 12 kg / Meals Served**
3. **Incoming Deliveries section**: *Arriving in 11 min — Arjun Sharma (Insulated Van)*
4. Point to partially-fulfilled need visual: *"We allocated 12 of the 20 kg lunch need. The remaining 8 kg stays open and will be matched to the next donor surplus. Needs are never artificially marked fulfilled short."*
5. Click **Verify Hand-off** → OTP modal appears: *"The receiver must enter the OTP the driver reads out."*
   - Enter **4729** → verified state
6. **(01:52)** Switch to **Tab 4 (Driver)**

### Segment 4 — Driver: handoff workflow (01:55 → 02:50)

> "This is Arjun Sharma, our driver. The Anna Sadan Trust stop is the next action on his mission."

1. Active Job tile: **Green Leaf Catering → 3 stops, ₹264 earnings, 9.1 km, 35 min**
2. Route stops list:
   - ✅ Stop 1 COMPLETED · Seva Community Kitchen 12 kg
   - 🔵 **Stop 2 IN PROGRESS · Anna Sadan Trust 8 kg ← NEXT ACTION**
   - ⚪ Stop 3 PENDING · Sahara Community Home 20 kg
3. **(02:15)** Large primary button: **"Verify delivery"** → click → OTP screen appears
   - Receiver gives OTP **4729** → driver enters
   - Seal integrity check → **Intact** (seal AS-GL-000047)
   - Evidence: package photo captured at each handoff
4. → Earnings today ₹264; ₹1850 pending payout week (show driver wallet summary)
5. Available jobs: one other job (Taj Express Banquets, 25 kg) — shows driver has choice
6. **(02:48)** Switch to **Tab 5 (Admin)**

### Segment 5 — Admin: operations console (02:50 → 03:40)

> "Admin Priya is running operations. The command center shows live metrics, a prioritized operations queue, verifications, and any integrity or operational exceptions."

1. Dashboard KPI row: **Active Donations / Open Needs / Live Routes / Pending Verifications / Healthy Match Rate**
2. Operations Queue (3 cards):
   - 🔴 High: New receiver verification (Care India Trust)
   - 🟡 Medium: **ETA delay alert on route AS-GL-0001** — Arjun Sharma, Golf Course Road congestion, deadline safe
   - 🔴 Critical: Donation AS-1049 expiring in 45 minutes
3. **Operational exception tile**: One delivery status `REASSIGNMENT_REQUIRED` (mechanical breakdown) — *"The system detected a driver-side exception, automatically reverted allocations, and re-posted offers."*
4. **Integrity review row**: One check status `REVIEW_REQUIRED` with admin note
5. Recent Activity timeline:
   - 2:30 PM Green Leaf Catering handed off 40 kg · OTP verified
   - 2:18 PM AS-GL-0001 matched to 3 receivers (Seva Community, Anna Sadan, Sahara)
   - 11:00 AM Donor Taj Banquets verified by Admin Priya

### Segment 6 — Demo controls & wrap (03:40 → 04:00)

> "The scenario is deterministic and resetable between demos."

1. Demo banner (top of every page if `NEXT_PUBLIC_DEMO_MODE=true`): *"Flask icon · Demo Environment · Seeded scenario resets between sessions"*
2. Admin → Demo controls: **POST /api/v1/admin/demo/reset?confirm=true** (requires DEMO_MODE + admin role + optional token)
3. **CLI demo reset** (one command anytime):
   ```bash
   cd backend && python scripts/seed_demo.py --reset
   ```
4. Close on impact: *"This 40 kg rescue becomes approximately 120 meals. Each kg is tracked, each handoff verified, each payout settled deterministically. That is the AnnaSetu guarantee."*

---

## Reset between demo runs

```bash
# Option A — CLI (fastest, includes credentials table):
cd backend
python scripts/seed_demo.py --reset

# Option B — HTTP (if backend is live and DEMO_MODE=true):
curl -X POST "http://localhost:8000/api/v1/admin/demo/reset?confirm=true" \
  -H "Authorization: Bearer <admin-jwt>" \
  -H "X-Demo-Reset-Token: DEMO_RESET_123456789"
```

---

## Failure-mode fallback (if backend unreachable during demo)

All 4 role portals ship with fully-consistent frontend mock data (same scenario IDs,
same names, same quantities, same seal ID `AS-GL-000047`, same OTP `4729`,
same payout ₹264 / wallet ₹480 / fee ₹96). The demo narrative works 100% offline
against the UI mock state — the only difference is API calls are silently swallowed
by console-warn fallbacks.
