"""Small helpers for the web UI: pagination, date parsing, and a 'next scan in…' string."""
from datetime import datetime, timezone

from .ingest.runner import _parse_date  # ISO 8601 / epoch-ms tolerant parser


def to_dt(s):
    return _parse_date(s)


def paginate(rows, page, per_page=20):
    """Slice `rows` for the given 1-based page. Returns (page_rows, meta)."""
    rows = list(rows)
    total = len(rows)
    pages = max(1, (total + per_page - 1) // per_page)
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1
    page = max(1, min(page, pages))
    start = (page - 1) * per_page
    meta = {"page": page, "pages": pages, "total": total, "per_page": per_page,
            "start": start + 1 if total else 0, "end": min(start + per_page, total)}
    return rows[start:start + per_page], meta


def human_until(dt) -> str:
    """'in 3h 12m' / 'in 14m' / 'due now' / 'off' from a tz-aware datetime."""
    if not dt:
        return "off"
    now = datetime.now(dt.tzinfo or timezone.utc)
    secs = int((dt - now).total_seconds())
    if secs <= 0:
        return "due now"
    h, m = secs // 3600, (secs % 3600) // 60
    if h >= 24:
        d = h // 24
        return f"in {d}d {h % 24}h"
    return f"in {h}h {m}m" if h else f"in {m}m"
