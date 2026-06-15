"""Parse CBF tables HTML into manual_source_batch_v0.

This parser is read-only by default. It extracts standings and aggregate cards
from a saved CBF HTML page and can emit a validated manual source batch.

Usage:
  python -m engine.ingestion.cbf_tabelas path/to/cbf.html --liga brasileirao_serie_b --season 2026 --round 13 --source-url https://...
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from .manual_source_batch import format_text_report, validate_batch


@dataclass(frozen=True)
class StandingRow:
    position: int
    team: str
    points: int
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    yellow_cards: int
    red_cards: int
    points_percentage: int


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[tuple[str, str]]]] = []
        self._in_table = False
        self._in_row = False
        self._in_cell = False
        self._cell_tag = ""
        self._table: list[list[tuple[str, str]]] = []
        self._row: list[tuple[str, str]] = []
        self._cell_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._in_table = True
            self._table = []
        elif self._in_table and tag == "tr":
            self._in_row = True
            self._row = []
        elif self._in_row and tag in {"td", "th"}:
            self._in_cell = True
            self._cell_tag = tag
            self._cell_parts = []

    def handle_endtag(self, tag: str) -> None:
        if self._in_cell and tag == self._cell_tag:
            text = " ".join("".join(self._cell_parts).split())
            self._row.append((self._cell_tag, text))
            self._in_cell = False
            self._cell_tag = ""
        elif self._in_row and tag == "tr":
            self._table.append(self._row)
            self._in_row = False
            self._row = []
        elif self._in_table and tag == "table":
            self.tables.append(self._table)
            self._in_table = False
            self._table = []

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell_parts.append(data)


def parse_standings_html(html: str) -> list[StandingRow]:
    parser = _TableParser()
    parser.feed(html)
    for table in parser.tables:
        if _is_standings_table(table):
            return _parse_standings_table(table)
    return []


def build_manual_batch(
    rows: list[StandingRow],
    *,
    liga: str,
    season: int,
    round_number: int,
    source_url: str,
    fetched_at: str,
    snapshot_path: str | None,
    raw_payload_hash: str | None,
    created_by: str = "cbf_tabelas_parser",
) -> dict[str, Any]:
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    batch_id = f"cbf-{liga}-{season}-r{round_number}-standings"
    records: list[dict[str, Any]] = []
    for row in rows:
        team_key = _slug(row.team)
        evidence = {
            "page": None,
            "line": None,
            "selector": "table:classificacao",
            "quote": (
                f"{row.team} PTS {row.points} J {row.played} "
                f"GP {row.goals_for} GC {row.goals_against} CA {row.yellow_cards} CV {row.red_cards}"
            ),
            "table": "classificacao",
        }
        standings_payload = {
            "competition": liga,
            "season": season,
            "round": round_number,
            "position": row.position,
            "team": row.team,
            "points": row.points,
            "played": row.played,
            "wins": row.wins,
            "draws": row.draws,
            "losses": row.losses,
            "goals_for": row.goals_for,
            "goals_against": row.goals_against,
            "goal_difference": row.goal_difference,
            "yellow_cards": row.yellow_cards,
            "red_cards": row.red_cards,
            "points_percentage": row.points_percentage,
        }
        records.append(
            {
                "record_id": f"standings-{team_key}-{season}-r{round_number}",
                "record_type": "standings",
                "natural_key": f"{liga}:{season}:{round_number}:{team_key}:standings",
                "status": "ok",
                "quality_score": 4,
                "evidence": evidence,
                "payload": standings_payload,
            }
        )
        records.append(
            {
                "record_id": f"discipline-{team_key}-{season}-r{round_number}",
                "record_type": "discipline_team",
                "natural_key": f"{liga}:{season}:{round_number}:{team_key}:discipline_team",
                "status": "ok",
                "quality_score": 4,
                "evidence": evidence,
                "payload": {
                    "competition": liga,
                    "season": season,
                    "round": round_number,
                    "team": row.team,
                    "yellow_cards": row.yellow_cards,
                    "red_cards": row.red_cards,
                },
            }
        )

    return {
        "schema_version": "manual_source_batch_v0",
        "batch_id": batch_id,
        "created_at": created_at,
        "created_by": created_by,
        "notes": "Gerado por parser deterministico da tabela CBF HTML. Revisar antes de importar.",
        "source": {
            "source_id": "cbf_tabelas",
            "source_name": "CBF - Tabelas",
            "source_url": source_url,
            "source_type": "oficial_primaria",
            "fetched_at": fetched_at,
            "quality_score": 4,
            "status_fonte": "ativo",
            "ingestion_method": "scraper_html",
            "source_snapshot_path": snapshot_path,
            "raw_payload_hash": raw_payload_hash,
            "extraction_tool": "engine.ingestion.cbf_tabelas",
        },
        "records": records,
    }


def parse_file_to_batch(
    path: str | Path,
    *,
    liga: str,
    season: int,
    round_number: int,
    source_url: str,
    fetched_at: str,
) -> dict[str, Any]:
    file_path = Path(path)
    raw = file_path.read_bytes()
    html = raw.decode("utf-8", errors="ignore")
    rows = parse_standings_html(html)
    if not rows:
        raise ValueError("tabela de classificacao CBF nao encontrada")
    return build_manual_batch(
        rows,
        liga=liga,
        season=season,
        round_number=round_number,
        source_url=source_url,
        fetched_at=fetched_at,
        snapshot_path=str(file_path),
        raw_payload_hash="sha256:" + hashlib.sha256(raw).hexdigest(),
    )


def _is_standings_table(table: list[list[tuple[str, str]]]) -> bool:
    if not table:
        return False
    headers = [_normalize_header(text) for tag, text in table[0] if tag == "th"]
    joined = " ".join(headers)
    return (
        "classificacao" in joined
        and "pts" in joined
        and "jogos" in joined
        and "cartoes amarelos" in joined
        and "cartoes vermelhos" in joined
    )


def _parse_standings_table(table: list[list[tuple[str, str]]]) -> list[StandingRow]:
    rows: list[StandingRow] = []
    for raw_row in table[1:]:
        cells = [text for tag, text in raw_row if tag == "td"]
        if len(cells) < 12:
            continue
        position, team = _parse_team_cell(cells[0])
        rows.append(
            StandingRow(
                position=position,
                team=team,
                points=_int(cells[1]),
                played=_int(cells[2]),
                wins=_int(cells[3]),
                draws=_int(cells[4]),
                losses=_int(cells[5]),
                goals_for=_int(cells[6]),
                goals_against=_int(cells[7]),
                goal_difference=_int(cells[8]),
                yellow_cards=_int(cells[9]),
                red_cards=_int(cells[10]),
                points_percentage=_int(cells[11]),
            )
        )
    return rows


def _parse_team_cell(value: str) -> tuple[int, str]:
    value = value.strip()
    digits = ""
    for char in value:
        if char.isdigit():
            digits += char
        else:
            break
    if not digits:
        raise ValueError(f"posicao ausente na celula de time: {value!r}")
    team = value[len(digits):].strip()
    if not team:
        raise ValueError(f"time ausente na celula de classificacao: {value!r}")
    return int(digits), team


def _normalize_header(value: str) -> str:
    return (
        value.lower()
        .replace("ç", "c")
        .replace("ã", "a")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("õ", "o")
        .replace("â", "a")
        .replace("ê", "e")
    )


def _int(value: str) -> int:
    cleaned = value.strip().replace("%", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    return int(cleaned)


def _slug(value: str) -> str:
    normalized = _normalize_header(value)
    out = []
    previous_dash = False
    for char in normalized:
        if char.isalnum():
            out.append(char)
            previous_dash = False
        elif not previous_dash:
            out.append("-")
            previous_dash = True
    return "".join(out).strip("-")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extrai classificacao CBF HTML para manual_source_batch_v0")
    parser.add_argument("path", help="HTML salvo da pagina de tabelas da CBF")
    parser.add_argument("--liga", required=True, help="Ex: brasileirao_serie_a")
    parser.add_argument("--season", required=True, type=int)
    parser.add_argument("--round", required=True, type=int, dest="round_number")
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--fetched-at", required=True, help="Timestamp ISO da coleta")
    parser.add_argument("--out", help="Arquivo JSON de saida. Use '-' para stdout")
    args = parser.parse_args(argv)

    try:
        batch = parse_file_to_batch(
            args.path,
            liga=args.liga,
            season=args.season,
            round_number=args.round_number,
            source_url=args.source_url,
            fetched_at=args.fetched_at,
        )
    except (OSError, ValueError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2

    report = validate_batch(batch)
    if args.out:
        text = json.dumps(batch, ensure_ascii=False, indent=2)
        if args.out == "-":
            print(text)
            print(format_text_report(report), file=sys.stderr)
        else:
            Path(args.out).write_text(text + "\n", encoding="utf-8")
            print(format_text_report(report))
            print(f"batch_json: {args.out}")
    else:
        print(format_text_report(report))
        print(f"linhas_classificacao: {len(parse_standings_html(Path(args.path).read_text(encoding='utf-8', errors='ignore')))}")
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

