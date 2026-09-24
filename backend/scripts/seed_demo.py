#!/usr/bin/env python3
"""Safe, repeatable demo seed entrypoint for AnnaSetu (Phase 19).

Usage:
    # From the backend/ directory:
    python scripts/seed_demo.py            # seed the canonical scenario
    python scripts/seed_demo.py --reset    # reset demo data, then re-seed
    python scripts/seed_demo.py --only-reset  # only reset demo data (no re-seed)

Environment requirements (see backend/.env.example):
    APP_ENV=development    # never seeds in production
    DEMO_MODE=true         # explicit
    SUPABASE_URL + SUPABASE_SECRET_KEY  # when using real Supabase

When Supabase credentials are missing the script runs with an explicit
error and a non-zero exit code so CI/repro scripts fail fast.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings  # noqa: E402
from app.db.supabase import get_supabase_client  # noqa: E402
from app.services.demo_service import DemoService  # noqa: E402


def _preflight() -> None:
    problems: list[str] = []
    if settings.is_production:
        problems.append(f"APP_ENV={settings.APP_ENV!r} — refusing to touch production data.")
    if not settings.DEMO_MODE:
        problems.append("DEMO_MODE=false — set DEMO_MODE=true in backend/.env to seed demo data.")
    db = get_supabase_client()
    if not db.is_configured:
        problems.append(
            "Supabase credentials are not configured. Set SUPABASE_URL and SUPABASE_SECRET_KEY "
            "in backend/.env, or use the in-memory mock backend for UI-only demos."
        )
    if problems:
        print("AnnaSetu demo seed preflight FAILED:\n  - " + "\n  - ".join(problems), file=sys.stderr)
        print(
            "\nQuick setup (backend/.env):\n"
            "  APP_ENV=development\n"
            "  DEMO_MODE=true\n"
            "  SUPABASE_URL=...\n"
            "  SUPABASE_SECRET_KEY=...\n",
            file=sys.stderr,
        )
        sys.exit(2)


async def _run(reset_first: bool, only_reset: bool) -> None:
    _preflight()
    demo = DemoService(db=get_supabase_client())

    if reset_first or only_reset:
        print("→ Removing demo-owned records tagged with namespace", demo_service_module.NAMESPACE_VALUE)
        removed = await demo.reset_demo_data()
        print(json.dumps(removed, indent=2, default=str))

    if only_reset:
        print("\nDemo reset complete. No new data seeded.")
        return

    print("\n→ Seeding canonical scenario: Green Leaf Catering 40 kg vegetarian meals")
    summary = await demo.seed_demo_scenario()
    print(json.dumps(summary, indent=2, default=str))
    print("\nGolden demo credentials (DEMO_MODE only — never real users):")
    creds = [
        ("Donor",    "Green Leaf Catering",       "operations@greenleafcatering.demo"),
        ("Receiver", "Seva Community Kitchen",    "team@sevakitchen.demo"),
        ("Receiver", "Anna Sadan Charitable Trust", "trust@annasadan.demo"),
        ("Driver",   "Arjun Sharma",              "arjun.delivery@annasetu.demo"),
        ("Admin",    "AnnaSetu Demo Admin",       "demo-admin@annasetu.demo"),
    ]
    for role, name, email in creds:
        print(f"  · {role:<8} {name:<32} {email}")

    print(
        "\nGolden demo quick flow (see docs/HACKATHON_DEMO.md for full 3–5 minute script):\n"
        "  1. Receiver Seva Community Kitchen opens active needs\n"
        "  2. Green Leaf Catering donation (40 kg) is visible to the matching engine\n"
        "  3. Compatible matches appear for both receivers with Rescue Priority 88–94\n"
        "  4. Allocations of 12 kg + 8 kg already confirmed\n"
        "  5. Delivery " + summary["entities"]["delivery"].split(" · ")[0] + " assigned to Arjun Sharma\n"
        "  6. Pickup OTP + seal already verified; stop 2 (Seva Kitchen) is the next action\n"
        "  7. Wallet reservation ₹480.00 shown under receiver wallet\n"
        "  8. Admin console shows exception delivery and an integrity review queue item\n"
    )


# Lazy import so `--help` works without importing demo service module-level constants.
import app.services.demo_service as demo_service_module  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="Remove demo-owned data, then re-seed.")
    parser.add_argument("--only-reset", action="store_true", help="Remove demo-owned data only; do not re-seed.")
    args = parser.parse_args()
    asyncio.run(_run(reset_first=args.reset, only_reset=args.only_reset))


if __name__ == "__main__":
    main()
