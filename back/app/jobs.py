"""Scheduled jobs, run by GitHub Actions (or locally) with a direct database connection.

    python -m app.jobs daily     # US snapshot, opened instruments, FX rates
    python -m app.jobs catalog   # US instrument catalog (~13 Massive calls, ~2-3 minutes)

Needs DATABASE_URL and MASSIVE_API_KEY. Exits with status 1 if any step failed.
"""

import argparse
import json
import sys

from app.config import get_settings
from app.db import get_session
from app.services.refresh import catalog_refresh, daily_refresh

JOBS = {"daily": daily_refresh, "catalog": catalog_refresh}


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.jobs")
    parser.add_argument("job", choices=sorted(JOBS))
    job = JOBS[parser.parse_args().job]

    settings = get_settings()
    session = next(get_session())
    try:
        results = job(session, settings)
    finally:
        session.close()

    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 1 if any(v.startswith("error") for v in results.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
