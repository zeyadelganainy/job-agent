from datetime import datetime, timedelta, timezone

from jobagent import webutil


def test_paginate_basic():
    rows = list(range(45))
    p, m = webutil.paginate(rows, 1, 20)
    assert p == list(range(20)) and m["pages"] == 3 and m["total"] == 45
    assert m["start"] == 1 and m["end"] == 20
    p, m = webutil.paginate(rows, 3, 20)
    assert p == list(range(40, 45)) and m["page"] == 3 and m["end"] == 45


def test_paginate_clamps_and_empty():
    assert webutil.paginate(list(range(10)), 99, 20)[1]["page"] == 1
    p, m = webutil.paginate([], 1, 20)
    assert p == [] and m["pages"] == 1 and m["total"] == 0 and m["start"] == 0


def test_human_until():
    now = datetime.now(timezone.utc)
    assert webutil.human_until(None) == "off"
    assert webutil.human_until(now - timedelta(minutes=5)) == "due now"
    assert webutil.human_until(now + timedelta(hours=2, minutes=30)).startswith("in 2h")
    s = webutil.human_until(now + timedelta(minutes=20))
    assert s.endswith("m") and "h" not in s
