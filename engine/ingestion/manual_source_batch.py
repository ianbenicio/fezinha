"""Validate manual source batches before any database write.

Usage:
  python -m engine.ingestion.manual_source_batch path/to/batch.json
  python -m engine.ingestion.manual_source_batch path/to/batch.csv --format csv

The command is read-only. It never writes to Supabase.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "manual_source_batch_v0"

SOURCE_TYPES = {
    "oficial_primaria",
    "api_licenciada",
    "midia_confiavel",
    "clube_oficial",
    "mercado_odds",
    "meteorologia",
    "manual_operador",
    "social_ou_rumor",
}
SOURCE_STATUS = {"ativo", "manual", "futuro", "quarentena", "bloqueado"}
INGESTION_METHODS = {"manual_json", "manual_csv", "notebooklm", "scraper_html", "pdf", "api"}
RECORD_TYPES = {"standings", "fixture", "result", "discipline_team", "news", "odds", "absence"}
RECORD_STATUS = {"ok", "quarentena", "conflito", "rejeitado"}
FIXTURE_STATUS = {"scheduled", "finished", "postponed", "cancelled", "unknown"}
RESULT_STATUS = {"finished"}
ODDS_MARKETS = {"1x2", "over_under_gols", "escanteios", "btts", "handicap"}
ABSENCE_STATUS = {"out", "doubt", "suspended", "injured", "returned", "unknown"}

FACTUAL_RECORD_TYPES = {"standings", "fixture", "result", "discipline_team", "odds", "absence"}
SUSPECT_TERMS = (
    "provavelmente",
    "estima-se",
    "estimado",
    "inferido",
    "base no conhecimento",
    "conhecimento previo",
    "memoria",
    "nao consta mas",
    "nao consta, mas",
    "completado",
)

CSV_REQUIRED_COLUMNS = {
    "schema_version",
    "batch_id",
    "created_at",
    "created_by",
    "record_id",
    "record_type",
    "natural_key",
    "record_status",
    "record_quality_score",
    "source_id",
    "source_name",
    "source_url",
    "source_type",
    "fetched_at",
    "source_quality_score",
    "status_fonte",
    "ingestion_method",
    "source_snapshot_path",
    "raw_payload_hash",
    "evidence_json",
    "payload_json",
}


@dataclass
class Issue:
    path: str
    message: str


@dataclass
class RecordDecision:
    record_id: str
    record_type: str
    natural_key: str
    input_status: str
    decision: str
    reason: str


@dataclass
class ValidationReport:
    batch_id: str | None
    source_id: str | None
    errors: list[Issue]
    warnings: list[Issue]
    records: list[RecordDecision]
    writes_database: bool = False

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, path: str, message: str) -> None:
        self.errors.append(Issue(path, message))

    def warn(self, path: str, message: str) -> None:
        self.warnings.append(Issue(path, message))

    def as_dict(self) -> dict[str, Any]:
        counts = {
            "ok": 0,
            "quarentena": 0,
            "conflito": 0,
            "rejeitado": 0,
        }
        for record in self.records:
            counts[record.decision] = counts.get(record.decision, 0) + 1
        return {
            "batch_id": self.batch_id,
            "source_id": self.source_id,
            "ok": self.ok,
            "writes_database": self.writes_database,
            "counts": counts,
            "errors": [asdict(issue) for issue in self.errors],
            "warnings": [asdict(issue) for issue in self.warnings],
            "records": [asdict(record) for record in self.records],
        }


def validate_batch(payload: dict[str, Any]) -> ValidationReport:
    report = ValidationReport(
        batch_id=_str_or_none(payload.get("batch_id")) if isinstance(payload, dict) else None,
        source_id=None,
        errors=[],
        warnings=[],
        records=[],
    )

    if not isinstance(payload, dict):
        report.error("$", "payload deve ser objeto JSON")
        return report

    for i, msg in enumerate(payload.get("_load_errors", [])):
        report.error(f"_load_errors[{i}]", str(msg))

    _validate_top_level(payload, report)
    source = payload.get("source")
    if isinstance(source, dict):
        report.source_id = _str_or_none(source.get("source_id"))
        _validate_source(source, report)

    records = payload.get("records")
    if not isinstance(records, list):
        return report

    source_needs_quarantine = _source_needs_quarantine(source)
    source_quality = _number_or_none(source.get("quality_score")) if isinstance(source, dict) else None
    seen_record_ids: dict[str, int] = {}
    seen_natural_keys: dict[str, int] = {}

    for index, record in enumerate(records):
        path = f"records[{index}]"
        if not isinstance(record, dict):
            report.error(path, "registro deve ser objeto")
            continue

        before_errors = len(report.errors)
        record_id = _record_string(record, "record_id", path, report)
        record_type = _record_string(record, "record_type", path, report)
        natural_key = _record_string(record, "natural_key", path, report)
        input_status = _record_string(record, "status", path, report)
        record_quality = _required_quality(record, "quality_score", path, report)

        if record_id:
            if record_id in seen_record_ids:
                report.error(f"{path}.record_id", f"duplicado; primeiro uso em records[{seen_record_ids[record_id]}]")
            else:
                seen_record_ids[record_id] = index
        if natural_key:
            if natural_key in seen_natural_keys:
                report.error(
                    f"{path}.natural_key",
                    f"duplicado; primeiro uso em records[{seen_natural_keys[natural_key]}]",
                )
            else:
                seen_natural_keys[natural_key] = index

        if record_type and record_type not in RECORD_TYPES:
            report.error(f"{path}.record_type", f"tipo invalido: {record_type!r}")
        if input_status and input_status not in RECORD_STATUS:
            report.error(f"{path}.status", f"status invalido: {input_status!r}")

        evidence = record.get("evidence")
        _validate_evidence(evidence, f"{path}.evidence", report)

        payload_obj = record.get("payload")
        if not isinstance(payload_obj, dict):
            report.error(f"{path}.payload", "payload deve ser objeto")
        elif record_type in RECORD_TYPES:
            _validate_payload(record_type, payload_obj, f"{path}.payload", report)
            _scan_suspect_terms(payload_obj, f"{path}.payload", report, input_status == "ok")

        decision, reason = _decide_record(
            input_status=input_status,
            record_type=record_type,
            record_quality=record_quality,
            source_quality=source_quality,
            source_needs_quarantine=source_needs_quarantine,
            has_errors=len(report.errors) > before_errors,
        )
        report.records.append(
            RecordDecision(
                record_id=record_id or f"records[{index}]",
                record_type=record_type or "desconhecido",
                natural_key=natural_key or "",
                input_status=input_status or "desconhecido",
                decision=decision,
                reason=reason,
            )
        )

    return report


def load_batch(path: str | Path, fmt: str = "auto") -> dict[str, Any]:
    file_path = Path(path)
    chosen = fmt
    if chosen == "auto":
        chosen = "csv" if file_path.suffix.lower() == ".csv" else "json"
    if chosen == "csv":
        return _load_csv(file_path)
    if chosen != "json":
        raise ValueError(f"formato invalido: {fmt}")
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("payload JSON deve ser objeto")
    return data


def _load_csv(path: Path) -> dict[str, Any]:
    load_errors: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return {"_load_errors": ["CSV vazio"], "records": []}

    columns = set(rows[0])
    missing = sorted(CSV_REQUIRED_COLUMNS - columns)
    if missing:
        load_errors.append(f"CSV sem colunas obrigatorias: {', '.join(missing)}")

    first = rows[0]
    batch = {
        "schema_version": _csv_value(first.get("schema_version")),
        "batch_id": _csv_value(first.get("batch_id")),
        "created_at": _csv_value(first.get("created_at")),
        "created_by": _csv_value(first.get("created_by")),
        "notes": _csv_nullable(first.get("notes")),
        "source": {
            "source_id": _csv_value(first.get("source_id")),
            "source_name": _csv_value(first.get("source_name")),
            "source_url": _csv_value(first.get("source_url")),
            "source_type": _csv_value(first.get("source_type")),
            "fetched_at": _csv_value(first.get("fetched_at")),
            "quality_score": _csv_number(first.get("source_quality_score")),
            "status_fonte": _csv_value(first.get("status_fonte")),
            "ingestion_method": _csv_value(first.get("ingestion_method")) or "manual_csv",
            "source_snapshot_path": _csv_nullable(first.get("source_snapshot_path")),
            "raw_payload_hash": _csv_nullable(first.get("raw_payload_hash")),
            "extraction_tool": _csv_nullable(first.get("extraction_tool")),
        },
        "records": [],
        "_load_errors": load_errors,
    }

    stable_source_fields = [
        "source_id",
        "source_name",
        "source_url",
        "source_type",
        "fetched_at",
        "status_fonte",
        "source_snapshot_path",
        "raw_payload_hash",
    ]
    for index, row in enumerate(rows):
        for field in stable_source_fields:
            if _csv_value(row.get(field)) != _csv_value(first.get(field)):
                load_errors.append(f"linha {index + 2}: campo de fonte divergente: {field}")

        evidence = _parse_csv_json(row.get("evidence_json"), f"linha {index + 2}.evidence_json", load_errors)
        payload = _parse_csv_json(row.get("payload_json"), f"linha {index + 2}.payload_json", load_errors)
        batch["records"].append(
            {
                "record_id": _csv_value(row.get("record_id")),
                "record_type": _csv_value(row.get("record_type")),
                "natural_key": _csv_value(row.get("natural_key")),
                "status": _csv_value(row.get("record_status")),
                "quality_score": _csv_number(row.get("record_quality_score")),
                "evidence": evidence,
                "payload": payload,
            }
        )

    return batch


def _validate_top_level(payload: dict[str, Any], report: ValidationReport) -> None:
    _required_exact(payload, "schema_version", SCHEMA_VERSION, "$", report)
    _required_str(payload, "batch_id", "$", report)
    _required_timestamp(payload, "created_at", "$", report)
    _required_str(payload, "created_by", "$", report)
    if payload.get("notes") is not None and not isinstance(payload.get("notes"), str):
        report.error("$.notes", "deve ser string ou null")
    if not isinstance(payload.get("source"), dict):
        report.error("$.source", "objeto obrigatorio")
    if not isinstance(payload.get("records"), list) or not payload.get("records"):
        report.error("$.records", "lista obrigatoria com ao menos um registro")


def _validate_source(source: dict[str, Any], report: ValidationReport) -> None:
    _required_str(source, "source_id", "source", report)
    _required_str(source, "source_name", "source", report)
    _required_url(source, "source_url", "source", report)
    _required_enum(source, "source_type", SOURCE_TYPES, "source", report)
    _required_timestamp(source, "fetched_at", "source", report)
    _required_quality(source, "quality_score", "source", report)
    _required_enum(source, "status_fonte", SOURCE_STATUS, "source", report)
    _required_enum(source, "ingestion_method", INGESTION_METHODS, "source", report)
    _optional_str(source, "source_snapshot_path", "source", report)
    _optional_str(source, "raw_payload_hash", "source", report)
    _optional_str(source, "extraction_tool", "source", report)

    if not _nonempty_str(source.get("source_snapshot_path")) and not _nonempty_str(source.get("raw_payload_hash")):
        report.warn("source", "sem snapshot/hash; registros factuais devem ficar em quarentena")


def _validate_evidence(evidence: Any, path: str, report: ValidationReport) -> None:
    if not isinstance(evidence, dict):
        report.error(path, "evidence deve ser objeto")
        return

    has_evidence = False
    for key in ["selector", "quote", "table"]:
        value = evidence.get(key)
        if value is not None and not isinstance(value, str):
            report.error(f"{path}.{key}", "deve ser string ou null")
        if isinstance(value, str) and value.strip():
            has_evidence = True
    for key in ["page", "line"]:
        value = evidence.get(key)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 1):
            report.error(f"{path}.{key}", "deve ser inteiro >= 1 ou null")
        if isinstance(value, int) and not isinstance(value, bool) and value >= 1:
            has_evidence = True

    quote = evidence.get("quote")
    if isinstance(quote, str) and len(quote) > 300:
        report.error(f"{path}.quote", "deve ter no maximo 300 caracteres")
    if not has_evidence:
        report.error(path, "preencha ao menos page, line, selector, quote ou table")


def _validate_payload(record_type: str, payload: dict[str, Any], path: str, report: ValidationReport) -> None:
    if record_type == "standings":
        _validate_standings(payload, path, report)
    elif record_type == "fixture":
        _validate_fixture(payload, path, report)
    elif record_type == "result":
        _validate_result(payload, path, report)
    elif record_type == "discipline_team":
        _validate_discipline(payload, path, report)
    elif record_type == "news":
        _validate_news(payload, path, report)
    elif record_type == "odds":
        _validate_odds(payload, path, report)
    elif record_type == "absence":
        _validate_absence(payload, path, report)


def _validate_standings(payload: dict[str, Any], path: str, report: ValidationReport) -> None:
    _required_str(payload, "competition", path, report)
    _required_int(payload, "season", path, report, min_value=2000, max_value=2100)
    _required_int(payload, "round", path, report, min_value=1, max_value=100)
    _required_int(payload, "position", path, report, min_value=1, max_value=100)
    _required_str(payload, "team", path, report)
    for key in ["points", "played", "wins", "draws", "losses", "goals_for", "goals_against"]:
        _required_int(payload, key, path, report, min_value=0)
    _required_int(payload, "goal_difference", path, report, min_value=-200, max_value=200)
    _optional_int(payload, "yellow_cards", path, report, min_value=0)
    _optional_int(payload, "red_cards", path, report, min_value=0)
    _optional_number(payload, "points_percentage", path, report, min_value=0, max_value=100)


def _validate_fixture(payload: dict[str, Any], path: str, report: ValidationReport) -> None:
    _required_str(payload, "competition", path, report)
    _required_int(payload, "season", path, report, min_value=2000, max_value=2100)
    _required_int(payload, "round", path, report, min_value=1, max_value=100)
    _optional_date(payload, "match_date", path, report)
    _optional_time(payload, "kickoff_time", path, report)
    _optional_str(payload, "timezone", path, report)
    _required_str(payload, "home_team", path, report)
    _required_str(payload, "away_team", path, report)
    _optional_str(payload, "stadium", path, report)
    _required_enum(payload, "status", FIXTURE_STATUS, path, report)


def _validate_result(payload: dict[str, Any], path: str, report: ValidationReport) -> None:
    _required_str(payload, "competition", path, report)
    _required_int(payload, "season", path, report, min_value=2000, max_value=2100)
    _required_int(payload, "round", path, report, min_value=1, max_value=100)
    _required_str(payload, "home_team", path, report)
    _required_str(payload, "away_team", path, report)
    _required_int(payload, "home_goals", path, report, min_value=0, max_value=20)
    _required_int(payload, "away_goals", path, report, min_value=0, max_value=20)
    _required_enum(payload, "status", RESULT_STATUS, path, report)


def _validate_discipline(payload: dict[str, Any], path: str, report: ValidationReport) -> None:
    _required_str(payload, "competition", path, report)
    _required_int(payload, "season", path, report, min_value=2000, max_value=2100)
    _required_int(payload, "round", path, report, min_value=1, max_value=100)
    _required_str(payload, "team", path, report)
    _required_int(payload, "yellow_cards", path, report, min_value=0, max_value=300)
    _required_int(payload, "red_cards", path, report, min_value=0, max_value=100)


def _validate_news(payload: dict[str, Any], path: str, report: ValidationReport) -> None:
    _optional_str(payload, "competition", path, report)
    _optional_str(payload, "team", path, report)
    _required_str(payload, "title", path, report)
    _required_url(payload, "url", path, report)
    _optional_timestamp(payload, "published_at", path, report)
    _optional_str(payload, "summary", path, report)
    tags = payload.get("tags")
    if tags is not None:
        if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
            report.error(f"{path}.tags", "deve ser lista de strings ou null")


def _validate_odds(payload: dict[str, Any], path: str, report: ValidationReport) -> None:
    _required_str(payload, "competition", path, report)
    _required_int(payload, "season", path, report, min_value=2000, max_value=2100)
    _required_int(payload, "round", path, report, min_value=1, max_value=100)
    _required_str(payload, "home_team", path, report)
    _required_str(payload, "away_team", path, report)
    _required_str(payload, "bookmaker", path, report)
    _required_enum(payload, "market", ODDS_MARKETS, path, report)
    _required_str(payload, "selection", path, report)
    _optional_number(payload, "line", path, report, min_value=0)
    _required_number(payload, "odd", path, report, min_value=1.01)
    _required_timestamp(payload, "captured_at", path, report)


def _validate_absence(payload: dict[str, Any], path: str, report: ValidationReport) -> None:
    _required_str(payload, "competition", path, report)
    _required_int(payload, "season", path, report, min_value=2000, max_value=2100)
    _required_int(payload, "round", path, report, min_value=1, max_value=100)
    _required_str(payload, "team", path, report)
    _required_str(payload, "player", path, report)
    _required_str(payload, "reason", path, report)
    _required_enum(payload, "status", ABSENCE_STATUS, path, report)
    _optional_timestamp(payload, "valid_until", path, report)


def _decide_record(
    *,
    input_status: str,
    record_type: str,
    record_quality: float | None,
    source_quality: float | None,
    source_needs_quarantine: bool,
    has_errors: bool,
) -> tuple[str, str]:
    if has_errors or input_status == "rejeitado":
        return "rejeitado", "erro estrutural, status rejeitado ou dado invalido"
    if input_status == "conflito":
        return "conflito", "registro marcado como conflito"
    if input_status == "quarentena":
        return "quarentena", "registro marcado como quarentena"
    if source_needs_quarantine and record_type in FACTUAL_RECORD_TYPES:
        return "quarentena", "fonte sem snapshot/hash"
    if record_type in FACTUAL_RECORD_TYPES and ((source_quality is not None and source_quality < 4) or (record_quality is not None and record_quality < 4)):
        return "quarentena", "confiabilidade abaixo de 4 para dado factual"
    return "ok", "validacao estrutural concluida"


def format_text_report(report: ValidationReport) -> str:
    data = report.as_dict()
    counts = data["counts"]
    lines = [
        "Relatorio manual_source_batch_v0",
        f"batch_id: {report.batch_id or '-'}",
        f"source_id: {report.source_id or '-'}",
        "writes_database: false",
        f"resultado: {'OK' if report.ok else 'ERRO'}",
        (
            "registros: "
            f"ok={counts.get('ok', 0)} "
            f"quarentena={counts.get('quarentena', 0)} "
            f"conflito={counts.get('conflito', 0)} "
            f"rejeitado={counts.get('rejeitado', 0)}"
        ),
        "",
    ]
    if report.errors:
        lines.append("ERROS:")
        lines.extend(f"- {issue.path}: {issue.message}" for issue in report.errors)
        lines.append("")
    if report.warnings:
        lines.append("AVISOS:")
        lines.extend(f"- {issue.path}: {issue.message}" for issue in report.warnings)
        lines.append("")
    if report.records:
        lines.append("REGISTROS:")
        for record in report.records:
            lines.append(
                f"- {record.record_id} [{record.record_type}] -> {record.decision}: {record.reason}"
            )
        lines.append("")
    lines.append("Nenhuma escrita no banco foi executada.")
    return "\n".join(lines)


def _source_needs_quarantine(source: Any) -> bool:
    if not isinstance(source, dict):
        return True
    return not _nonempty_str(source.get("source_snapshot_path")) and not _nonempty_str(source.get("raw_payload_hash"))


def _scan_suspect_terms(value: Any, path: str, report: ValidationReport, is_factual_ok: bool) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _scan_suspect_terms(item, f"{path}.{key}", report, is_factual_ok)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _scan_suspect_terms(item, f"{path}[{index}]", report, is_factual_ok)
        return
    if not isinstance(value, str):
        return

    lowered = value.lower()
    for term in SUSPECT_TERMS:
        if term in lowered:
            message = f"termo indica inferencia ou completamento: {term!r}; use null se nao estiver na fonte"
            if is_factual_ok:
                report.error(path, message)
            else:
                report.warn(path, message)
            return


def _record_string(record: dict[str, Any], key: str, path: str, report: ValidationReport) -> str:
    _required_str(record, key, path, report)
    return record.get(key) if isinstance(record.get(key), str) else ""


def _required_exact(item: dict[str, Any], key: str, expected: str, path: str, report: ValidationReport) -> None:
    value = item.get(key)
    if value != expected:
        report.error(f"{path}.{key}", f"deve ser {expected!r}")


def _required_str(item: dict[str, Any], key: str, path: str, report: ValidationReport) -> None:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        report.error(f"{path}.{key}", "string obrigatoria")


def _optional_str(item: dict[str, Any], key: str, path: str, report: ValidationReport) -> None:
    value = item.get(key)
    if value is not None and not isinstance(value, str):
        report.error(f"{path}.{key}", "deve ser string ou null")


def _required_enum(item: dict[str, Any], key: str, values: set[str], path: str, report: ValidationReport) -> None:
    value = item.get(key)
    if value not in values:
        report.error(f"{path}.{key}", f"valor invalido: {value!r}; use {sorted(values)}")


def _required_int(
    item: dict[str, Any],
    key: str,
    path: str,
    report: ValidationReport,
    min_value: int | None = None,
    max_value: int | None = None,
) -> None:
    value = item.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        report.error(f"{path}.{key}", "inteiro obrigatorio")
        return
    _check_number_range(float(value), key, path, report, min_value, max_value)


def _optional_int(
    item: dict[str, Any],
    key: str,
    path: str,
    report: ValidationReport,
    min_value: int | None = None,
    max_value: int | None = None,
) -> None:
    value = item.get(key)
    if value is None:
        return
    if not isinstance(value, int) or isinstance(value, bool):
        report.error(f"{path}.{key}", "deve ser inteiro ou null")
        return
    _check_number_range(float(value), key, path, report, min_value, max_value)


def _required_number(
    item: dict[str, Any],
    key: str,
    path: str,
    report: ValidationReport,
    min_value: float | None = None,
    max_value: float | None = None,
) -> None:
    value = item.get(key)
    if not _is_number(value):
        report.error(f"{path}.{key}", "numero obrigatorio")
        return
    _check_number_range(float(value), key, path, report, min_value, max_value)


def _optional_number(
    item: dict[str, Any],
    key: str,
    path: str,
    report: ValidationReport,
    min_value: float | None = None,
    max_value: float | None = None,
) -> None:
    value = item.get(key)
    if value is None:
        return
    if not _is_number(value):
        report.error(f"{path}.{key}", "deve ser numero ou null")
        return
    _check_number_range(float(value), key, path, report, min_value, max_value)


def _required_quality(item: dict[str, Any], key: str, path: str, report: ValidationReport) -> float | None:
    value = item.get(key)
    if not _is_number(value):
        report.error(f"{path}.{key}", "numero 0..5 obrigatorio")
        return None
    value_f = float(value)
    if not 0 <= value_f <= 5:
        report.error(f"{path}.{key}", "deve estar entre 0 e 5")
    return value_f


def _required_url(item: dict[str, Any], key: str, path: str, report: ValidationReport) -> None:
    value = item.get(key)
    if not isinstance(value, str) or not value.startswith(("http://", "https://")):
        report.error(f"{path}.{key}", "URL obrigatoria com http:// ou https://")


def _required_timestamp(item: dict[str, Any], key: str, path: str, report: ValidationReport) -> None:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        report.error(f"{path}.{key}", "timestamp ISO obrigatorio")
        return
    if _parse_datetime(value) is None:
        report.error(f"{path}.{key}", "timestamp ISO invalido")


def _optional_timestamp(item: dict[str, Any], key: str, path: str, report: ValidationReport) -> None:
    value = item.get(key)
    if value is None:
        return
    if not isinstance(value, str) or not value.strip():
        report.error(f"{path}.{key}", "deve ser timestamp ISO ou null")
        return
    if _parse_datetime(value) is None:
        report.error(f"{path}.{key}", "timestamp ISO invalido")


def _optional_date(item: dict[str, Any], key: str, path: str, report: ValidationReport) -> None:
    value = item.get(key)
    if value is None:
        return
    if not isinstance(value, str) or not value.strip():
        report.error(f"{path}.{key}", "deve ser data ISO ou null")
        return
    try:
        date.fromisoformat(value)
    except ValueError:
        report.error(f"{path}.{key}", "data ISO invalida")


def _optional_time(item: dict[str, Any], key: str, path: str, report: ValidationReport) -> None:
    value = item.get(key)
    if value is None:
        return
    if not isinstance(value, str) or not re.fullmatch(r"\d{2}:\d{2}", value):
        report.error(f"{path}.{key}", "deve ser HH:MM ou null")


def _parse_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _check_number_range(
    value: float,
    key: str,
    path: str,
    report: ValidationReport,
    min_value: float | None,
    max_value: float | None,
) -> None:
    if min_value is not None and value < min_value:
        report.error(f"{path}.{key}", f"deve ser >= {min_value}")
    if max_value is not None and value > max_value:
        report.error(f"{path}.{key}", f"deve ser <= {max_value}")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _number_or_none(value: Any) -> float | None:
    if _is_number(value):
        return float(value)
    return None


def _str_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _csv_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _csv_nullable(value: Any) -> str | None:
    text = _csv_value(value)
    if not text or text.lower() == "null":
        return None
    return text


def _csv_number(value: Any) -> float | None:
    text = _csv_value(value)
    if not text or text.lower() == "null":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_csv_json(value: Any, path: str, errors: list[str]) -> Any:
    text = _csv_value(value)
    if not text:
        errors.append(f"{path}: JSON ausente")
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        errors.append(f"{path}: JSON invalido ({exc})")
        return {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Valida lote manual de fonte do Fezinha")
    parser.add_argument("path", help="Arquivo JSON ou CSV do lote")
    parser.add_argument("--format", choices=["auto", "json", "csv"], default="auto")
    parser.add_argument("--json-report", action="store_true", help="Imprimir relatorio como JSON")
    args = parser.parse_args(argv)

    try:
        payload = load_batch(args.path, args.format)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERRO: nao foi possivel ler lote: {exc}", file=sys.stderr)
        return 2

    report = validate_batch(payload)
    if args.json_report:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    else:
        print(format_text_report(report))
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

