from collections.abc import Sequence
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Base

# Postgres accepts at most 65,535 bind parameters per statement.
MAX_PARAMS = 60_000


def upsert(
    session: Session,
    model: type[Base],
    rows: Sequence[dict[str, Any]],
    keys: Sequence[str],
    update: Sequence[str],
) -> None:
    """INSERT ... ON CONFLICT (keys) DO UPDATE SET update..., chunked to fit Postgres limits.

    Rows sharing the same key are deduplicated (last one wins): Postgres refuses to update
    the same row twice in one statement.
    """
    if not rows:
        return
    rows = list({tuple(r[k] for k in keys): r for r in rows}.values())
    chunk = max(1, MAX_PARAMS // len(rows[0]))
    for i in range(0, len(rows), chunk):
        stmt = insert(model).values(list(rows[i : i + chunk]))
        if update:
            stmt = stmt.on_conflict_do_update(
                index_elements=list(keys), set_={c: stmt.excluded[c] for c in update}
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=list(keys))
        session.execute(stmt)


PRICE_COLUMNS = ("open", "high", "low", "close", "volume")
