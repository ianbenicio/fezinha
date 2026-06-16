"""Tests for manual_source_batch_v0 validation.

Run: python -m engine.test_manual_source_batch
"""
from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

from .ingestion.manual_source_batch import load_batch, validate_batch


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "docs" / "templates" / "manual_source_batch_v0.example.json"


def _example() -> dict:
    with EXAMPLE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict)
    return data


def test_example_template_is_valid():
    report = validate_batch(_example())
    assert not report.errors
    assert any(record.decision == "ok" for record in report.records)
    assert any(record.decision == "quarentena" for record in report.records)


def test_missing_source_url_rejects_factual_records():
    data = _example()
    data["source"]["source_url"] = ""
    report = validate_batch(data)
    assert report.errors
    assert any(issue.path == "source.source_url" for issue in report.errors)


def test_duplicate_natural_key_is_error():
    data = _example()
    data["records"][1]["natural_key"] = data["records"][0]["natural_key"]
    report = validate_batch(data)
    assert report.errors
    assert any("duplicado" in issue.message for issue in report.errors)


def test_conflict_record_is_reported_without_import_ok():
    data = _example()
    data["records"][0]["status"] = "conflito"
    report = validate_batch(data)
    assert not report.errors
    assert report.records[0].decision == "conflito"


def test_inferred_value_in_ok_record_is_error():
    data = _example()
    data["records"][0]["payload"]["team"] = "Palmeiras provavelmente"
    report = validate_batch(data)
    assert report.errors
    assert any("inferencia" in issue.message for issue in report.errors)


def test_csv_loader_builds_batch():
    evidence = json.dumps({"quote": "Time A 1 x 0 Time B"})
    payload = json.dumps(
        {
            "competition": "brasileirao_serie_a",
            "season": 2026,
            "round": 1,
            "home_team": "Time A",
            "away_team": "Time B",
            "home_goals": 1,
            "away_goals": 0,
            "status": "finished",
        }
    )
    csv_text = (
        "schema_version,batch_id,created_at,created_by,record_id,record_type,natural_key,"
        "record_status,record_quality_score,source_id,source_name,source_url,source_type,"
        "fetched_at,source_quality_score,status_fonte,ingestion_method,source_snapshot_path,"
        "raw_payload_hash,evidence_json,payload_json\n"
        "manual_source_batch_v0,batch-csv,2026-06-15T12:00:00-03:00,teste,"
        "result-1,result,liga:2026:1:time-a:time-b:result,ok,4,cbf_tabelas,CBF,"
        "https://www.cbf.com.br/,oficial_primaria,2026-06-15T12:00:00-03:00,4,ativo,"
        f"manual_csv,F:/snap.html,,\"{evidence.replace(chr(34), chr(34) + chr(34))}\","
        f"\"{payload.replace(chr(34), chr(34) + chr(34))}\"\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "batch.csv"
        path.write_text(csv_text, encoding="utf-8")
        batch = load_batch(path, "csv")

    report = validate_batch(batch)
    assert not report.errors
    assert report.records[0].decision == "ok"


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
