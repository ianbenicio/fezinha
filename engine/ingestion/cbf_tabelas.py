"""Parse CBF table pages into manual_source_batch_v0.

The command is read-only for the database. It can read a saved CBF HTML file or
download a URL into a local snapshot, then emit/validate a manual source batch.

Examples:
  python -m engine.ingestion.cbf_tabelas cbf.html --liga brasileirao_serie_b --season 2026 --round 13 --source-url https://...
  python -m engine.ingestion.cbf_tabelas https://www.cbf.com.br/.../serie-b/2026 --liga brasileirao_serie_b --season 2026 --round 13
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from .manual_source_batch import format_text_report, validate_batch


UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


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


@dataclass(frozen=True)
class MatchRow:
    game_number: str | None
    home_team: str
    away_team: str
    home_goals: int | None
    away_goals: int | None
    match_date: str | None
    kickoff_time: str | None
    city_state: str | None
    stadium: str | None
    document_url: str | None


@dataclass(frozen=True)
class HtmlSource:
    html: str
    snapshot_path: str
    raw_payload_hash: str
    source_url: str
    fetched_at: str


@dataclass
class _GameCard:
    teams: list[str]
    goals: list[int]
    game_number: str | None
    info_text: str
    document_url: str | None


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


class _GameCardParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.cards: list[_GameCard] = []
        self._in_card = False
        self._depth = 0
        self._card: _GameCard | None = None
        self._capture: str | None = None
        self._capture_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        class_name = attrs_dict.get("class") or ""

        if tag == "div" and "gameCardContainer" in class_name and not self._in_card:
            self._in_card = True
            self._depth = 1
            self._card = _GameCard(teams=[], goals=[], game_number=None, info_text="", document_url=None)
            return

        if not self._in_card:
            return

        if tag not in VOID_TAGS:
            self._depth += 1

        if tag == "strong" and attrs_dict.get("title") and self._card:
            self._card.teams.append(str(attrs_dict["title"]).strip())
        elif tag == "span" and "styles_gol__" in class_name:
            self._start_capture("goal")
        elif tag == "span" and "numberGame" in class_name:
            self._start_capture("game_number")
        elif tag == "p":
            self._start_capture("info")
        elif tag == "br" and self._capture == "info":
            self._capture_parts.append("\n")
        elif tag == "a" and attrs_dict.get("href") and "/futebol-brasileiro/jogos/" in str(attrs_dict["href"]):
            if self._card and not self._card.document_url:
                self._card.document_url = str(attrs_dict["href"])

    def handle_endtag(self, tag: str) -> None:
        if not self._in_card:
            return

        if self._capture == "goal" and tag == "span":
            text = "".join(self._capture_parts).strip()
            if text and self._card:
                self._card.goals.append(int(text))
            self._end_capture()
        elif self._capture == "game_number" and tag == "span":
            text = " ".join("".join(self._capture_parts).split())
            if self._card:
                self._card.game_number = text or None
            self._end_capture()
        elif self._capture == "info" and tag == "p":
            text = "\n".join(line.strip() for line in "".join(self._capture_parts).splitlines() if line.strip())
            if self._card:
                self._card.info_text = text
            self._end_capture()

        if tag not in VOID_TAGS:
            self._depth -= 1
            if self._depth == 0:
                if self._card:
                    self.cards.append(self._card)
                self._in_card = False
                self._card = None

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._capture_parts.append(data)

    def _start_capture(self, kind: str) -> None:
        self._capture = kind
        self._capture_parts = []

    def _end_capture(self) -> None:
        self._capture = None
        self._capture_parts = []


def parse_standings_html(html: str) -> list[StandingRow]:
    parser = _TableParser()
    parser.feed(html)
    for table in parser.tables:
        if _is_standings_table(table):
            return _parse_standings_table(table)
    return []


def parse_matches_html(html: str) -> list[MatchRow]:
    parser = _GameCardParser()
    parser.feed(html)
    matches: list[MatchRow] = []
    for card in parser.cards:
        if len(card.teams) < 2:
            continue
        match_date, kickoff_time, city_state, stadium = _parse_game_info(card.info_text)
        home_goals: int | None = None
        away_goals: int | None = None
        if len(card.goals) >= 2:
            home_goals, away_goals = card.goals[0], card.goals[1]
        matches.append(
            MatchRow(
                game_number=card.game_number,
                home_team=card.teams[0],
                away_team=card.teams[1],
                home_goals=home_goals,
                away_goals=away_goals,
                match_date=match_date,
                kickoff_time=kickoff_time,
                city_state=city_state,
                stadium=stadium,
                document_url=card.document_url,
            )
        )
    return matches


def load_html_source(
    source: str,
    *,
    source_url: str | None = None,
    fetched_at: str | None = None,
    snapshot_dir: str | Path = "var/ingestion/snapshots",
) -> HtmlSource:
    fetched = fetched_at or datetime.now().astimezone().isoformat(timespec="seconds")
    if _is_url(source):
        return _download_html(source, fetched_at=fetched, snapshot_dir=snapshot_dir)

    file_path = Path(source)
    raw = file_path.read_bytes()
    html = raw.decode("utf-8", errors="ignore")
    if not source_url:
        raise ValueError("source_url e obrigatorio quando a entrada e arquivo local")
    if not fetched_at:
        fetched = datetime.fromtimestamp(file_path.stat().st_mtime).astimezone().isoformat(timespec="seconds")
    return HtmlSource(
        html=html,
        snapshot_path=str(file_path),
        raw_payload_hash="sha256:" + hashlib.sha256(raw).hexdigest(),
        source_url=source_url,
        fetched_at=fetched,
    )


def build_manual_batch(
    standings: list[StandingRow],
    *,
    liga: str,
    season: int,
    round_number: int,
    source_url: str,
    fetched_at: str,
    snapshot_path: str | None,
    raw_payload_hash: str | None,
    matches: list[MatchRow] | None = None,
    created_by: str = "cbf_tabelas_parser",
) -> dict[str, Any]:
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    batch_id = f"cbf-{liga}-{season}-r{round_number}"
    records: list[dict[str, Any]] = []

    for row in standings:
        records.extend(_standing_records(row, liga=liga, season=season, round_number=round_number))
    for match in matches or []:
        records.append(_match_record(match, liga=liga, season=season, round_number=round_number))

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


def parse_source_to_batch(
    source: str,
    *,
    liga: str,
    season: int,
    round_number: int,
    source_url: str | None = None,
    fetched_at: str | None = None,
    snapshot_dir: str | Path = "var/ingestion/snapshots",
) -> dict[str, Any]:
    html_source = load_html_source(source, source_url=source_url, fetched_at=fetched_at, snapshot_dir=snapshot_dir)
    standings = parse_standings_html(html_source.html)
    matches = parse_matches_html(html_source.html)
    if not standings and not matches:
        raise ValueError("classificacao ou jogos CBF nao encontrados")
    return build_manual_batch(
        standings,
        liga=liga,
        season=season,
        round_number=round_number,
        source_url=html_source.source_url,
        fetched_at=html_source.fetched_at,
        snapshot_path=html_source.snapshot_path,
        raw_payload_hash=html_source.raw_payload_hash,
        matches=matches,
    )


def parse_file_to_batch(
    path: str | Path,
    *,
    liga: str,
    season: int,
    round_number: int,
    source_url: str,
    fetched_at: str,
) -> dict[str, Any]:
    return parse_source_to_batch(
        str(path),
        liga=liga,
        season=season,
        round_number=round_number,
        source_url=source_url,
        fetched_at=fetched_at,
    )


def _standing_records(row: StandingRow, *, liga: str, season: int, round_number: int) -> list[dict[str, Any]]:
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
    return [
        {
            "record_id": f"standings-{team_key}-{season}-r{round_number}",
            "record_type": "standings",
            "natural_key": f"{liga}:{season}:{round_number}:{team_key}:standings",
            "status": "ok",
            "quality_score": 4,
            "evidence": evidence,
            "payload": {
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
            },
        },
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
        },
    ]


def _match_record(match: MatchRow, *, liga: str, season: int, round_number: int) -> dict[str, Any]:
    home_key = _slug(match.home_team)
    away_key = _slug(match.away_team)
    is_finished = match.home_goals is not None and match.away_goals is not None
    score = f"{match.home_goals} x {match.away_goals}" if is_finished else "x"
    evidence = {
        "page": None,
        "line": None,
        "selector": "div:gameCardContainer",
        "quote": f"{match.home_team} {score} {match.away_team}",
        "table": "jogos",
    }
    common = {
        "competition": liga,
        "season": season,
        "round": round_number,
        "home_team": match.home_team,
        "away_team": match.away_team,
    }
    if is_finished:
        return {
            "record_id": f"result-{home_key}-{away_key}-{season}-r{round_number}",
            "record_type": "result",
            "natural_key": f"{liga}:{season}:{round_number}:{home_key}:{away_key}:result",
            "status": "ok",
            "quality_score": 4,
            "evidence": evidence,
            "payload": {
                **common,
                "home_goals": match.home_goals,
                "away_goals": match.away_goals,
                "status": "finished",
            },
        }
    return {
        "record_id": f"fixture-{home_key}-{away_key}-{season}-r{round_number}",
        "record_type": "fixture",
        "natural_key": f"{liga}:{season}:{round_number}:{home_key}:{away_key}:fixture",
        "status": "ok",
        "quality_score": 4,
        "evidence": evidence,
        "payload": {
            **common,
            "match_date": match.match_date,
            "kickoff_time": match.kickoff_time,
            "timezone": "America/Sao_Paulo",
            "stadium": match.stadium,
            "status": "scheduled",
        },
    }


def _download_html(url: str, *, fetched_at: str, snapshot_dir: str | Path) -> HtmlSource:
    import httpx

    response = httpx.get(url, headers={"User-Agent": UA}, timeout=30, follow_redirects=True)
    response.raise_for_status()
    raw = response.content
    digest = hashlib.sha256(raw).hexdigest()
    target_dir = Path(snapshot_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"cbf_tabelas_{_filename_timestamp(fetched_at)}_{digest[:12]}.html"
    path.write_bytes(raw)
    return HtmlSource(
        html=raw.decode(response.encoding or "utf-8", errors="ignore"),
        snapshot_path=str(path),
        raw_payload_hash="sha256:" + digest,
        source_url=url,
        fetched_at=fetched_at,
    )


def _is_standings_table(table: list[list[tuple[str, str]]]) -> bool:
    if not table:
        return False
    headers = [_normalize(text) for tag, text in table[0] if tag == "th"]
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


def _parse_game_info(info_text: str) -> tuple[str | None, str | None, str | None, str | None]:
    lines = [line.strip() for line in info_text.splitlines() if line.strip()]
    match_date = kickoff_time = city_state = stadium = None
    if lines:
        match_date, kickoff_time = _parse_date_time(lines[0])
    if len(lines) >= 2:
        city_state = lines[1]
    if len(lines) >= 3:
        stadium = lines[2]
    return match_date, kickoff_time, city_state, stadium


def _parse_date_time(value: str) -> tuple[str | None, str | None]:
    match = re.search(r"(\d{2})/(\d{2})/(\d{4})\s*-\s*(\d{2}:\d{2})", value)
    if not match:
        return None, None
    day, month, year, hour = match.groups()
    return f"{year}-{month}-{day}", hour


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


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).lower()


def _int(value: str) -> int:
    cleaned = value.strip().replace("%", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    return int(cleaned)


def _slug(value: str) -> str:
    normalized = _normalize(value)
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


def _is_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def _filename_timestamp(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "-", value).strip("-")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extrai pagina CBF para manual_source_batch_v0")
    parser.add_argument("source", help="HTML salvo ou URL da pagina de tabelas da CBF")
    parser.add_argument("--liga", required=True, help="Ex: brasileirao_serie_a")
    parser.add_argument("--season", required=True, type=int)
    parser.add_argument("--round", required=True, type=int, dest="round_number")
    parser.add_argument("--source-url", help="URL original; obrigatoria quando source e arquivo local")
    parser.add_argument("--fetched-at", help="Timestamp ISO da coleta; se omitido, usa agora ou mtime do arquivo")
    parser.add_argument("--snapshot-dir", default="var/ingestion/snapshots")
    parser.add_argument("--out", help="Arquivo JSON de saida. Use '-' para stdout")
    args = parser.parse_args(argv)

    try:
        batch = parse_source_to_batch(
            args.source,
            liga=args.liga,
            season=args.season,
            round_number=args.round_number,
            source_url=args.source_url,
            fetched_at=args.fetched_at,
            snapshot_dir=args.snapshot_dir,
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
        counts = _count_records(batch)
        print(f"linhas_classificacao: {counts['standings']}")
        print(f"jogos_resultados: {counts['fixture'] + counts['result']}")
    return 1 if report.errors else 0


def _count_records(batch: dict[str, Any]) -> dict[str, int]:
    counts = {"standings": 0, "fixture": 0, "result": 0, "discipline_team": 0}
    for record in batch.get("records", []):
        if isinstance(record, dict):
            record_type = record.get("record_type")
            if record_type in counts:
                counts[record_type] += 1
    return counts


if __name__ == "__main__":
    raise SystemExit(main())

