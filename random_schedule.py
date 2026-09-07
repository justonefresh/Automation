#!/usr/bin/env python3
"""Select exactly 100 private, deterministic five-minute UTC slots per day."""

import argparse
import hashlib
import hmac
import os
from datetime import datetime, timezone


SLOTS_PER_DAY = 24 * 60 // 5
SELECTED_SLOTS = 100


def selected_slots(day: str) -> list[int]:
    """Return the same shuffled slots for a day on every workflow runner."""
    seed = os.environ.get("SCHEDULE_SEED", "Automation-default-schedule").encode()
    ranked_slots = sorted(
        range(SLOTS_PER_DAY),
        key=lambda slot: hmac.new(
            seed, f"{day}:{slot}".encode(), hashlib.sha256
        ).digest(),
    )
    return sorted(ranked_slots[:SELECTED_SLOTS])


def should_run(now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    current_slot = now.hour * 12 + now.minute // 5
    return current_slot in selected_slots(now.date().isoformat())


def timestamps(day: str) -> list[str]:
    return [
        f"{slot // 12:02d}:{(slot % 12) * 5:02d} UTC"
        for slot in selected_slots(day)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Always run, for manual workflow dispatches",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Print the selected timestamps for today",
    )
    args = parser.parse_args()
    today = datetime.now(timezone.utc).date().isoformat()
    if args.show:
        print("\n".join(timestamps(today)))
    else:
        print("true" if args.force or should_run() else "false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())