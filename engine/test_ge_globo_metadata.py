"""Tests for ge.globo ingestion metadata helpers.

Run: python -m engine.test_ge_globo_metadata
"""
from __future__ import annotations

from .ingestion.ge_globo import _with_source_meta


def test_with_source_meta_preserves_existing_characteristics():
    car = {"ataque": 1.1, "_fontes": {"old": {"source_id": "old"}}}
    out = _with_source_meta(car, "brasileirao_serie_a", ["classificacao", "forma"], "2026-06-15T12:00:00+00:00")
    assert out["ataque"] == 1.1
    assert "old" in out["_fontes"]
    assert out["_fontes"]["ge_globo"]["quality_score"] == 3
    assert out["_fontes"]["ge_globo"]["fields"] == ["classificacao", "forma"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for fn in fns:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {fn.__name__}: {exc}")
    print(f"\n{len(fns) - failures}/{len(fns)} passaram")
    raise SystemExit(1 if failures else 0)

