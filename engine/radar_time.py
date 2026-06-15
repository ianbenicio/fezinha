"""Team radar payloads for explanatory UI.

Radar output is informational. It does not feed the match aggregator, EV,
stake, or betting recommendation.
"""
from __future__ import annotations

import math
import unicodedata
from dataclasses import dataclass
from typing import Any

from .ingestion.manual_source_batch import validate_batch


AXES = [
    ("forca_ofensiva", "Forca ofensiva"),
    ("solidez_defensiva", "Solidez defensiva"),
    ("forma_recente", "Forma recente"),
    ("consistencia", "Consistencia"),
    ("contexto_casa_fora", "Contexto casa/fora"),
    ("controle_disciplinar", "Controle disciplinar"),
]


@dataclass(frozen=True)
class TeamResult:
    index: int
    team: str
    opponent: str
    is_home: bool
    points: int
    goal_diff: int
    match_date: str | None


def build_radars_from_manual_batch(
    batch: dict[str, Any],
    *,
    contexto: str = "geral",
) -> dict[str, dict[str, Any]]:
    """Build one radar payload per team found in standings records."""
    report = validate_batch(batch)
    if report.errors:
        messages = "; ".join(f"{issue.path}: {issue.message}" for issue in report.errors[:5])
        raise ValueError(f"lote manual_source_batch_v0 invalido: {messages}")

    standings = _standings_by_team(batch)
    discipline = _discipline_by_team(batch)
    results = _results_by_team(batch)
    source = batch.get("source") or {}

    offense_values = _per_played_metric(standings, "goals_for")
    defense_values = _per_played_metric(standings, "goals_against")
    discipline_values = _discipline_metric(standings, discipline)

    radars: dict[str, dict[str, Any]] = {}
    for team_key, row in standings.items():
        team_name = str(row.get("team") or team_key)
        axes = [
            _standings_axis(
                axis_id="forca_ofensiva",
                label="Forca ofensiva",
                team_key=team_key,
                values=offense_values,
                invert=False,
                raw_label="gols_por_jogo",
                source=source,
                row=row,
            ),
            _standings_axis(
                axis_id="solidez_defensiva",
                label="Solidez defensiva",
                team_key=team_key,
                values=defense_values,
                invert=True,
                raw_label="gols_sofridos_por_jogo",
                source=source,
                row=row,
            ),
            _form_axis(team_key, results.get(team_key, []), source),
            _consistency_axis(team_key, results.get(team_key, []), source),
            _context_axis(team_key, results.get(team_key, []), source, contexto=contexto),
            _discipline_axis(team_key, discipline_values, source, row),
        ]
        radars[team_key] = {
            "schema_version": "radar_time_v0",
            "team": {
                "id": team_key,
                "nome": team_name,
                "liga": row.get("competition"),
            },
            "referencia": {
                "liga": row.get("competition"),
                "temporada": row.get("season"),
                "rodada": row.get("round"),
            },
            "contexto": contexto,
            "eixos": axes,
            "meta": {
                "uso": "explicativo",
                "entra_no_agregador": False,
                "fonte_base": source.get("source_id"),
                "fetched_at": source.get("fetched_at"),
            },
        }
    return radars


def build_radar_for_team(batch: dict[str, Any], team: str, *, contexto: str = "geral") -> dict[str, Any]:
    radars = build_radars_from_manual_batch(batch, contexto=contexto)
    key = _slug(team)
    if key not in radars:
        raise KeyError(f"time nao encontrado no lote: {team}")
    return radars[key]


def _standings_by_team(batch: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for record in batch.get("records", []):
        if not isinstance(record, dict) or record.get("record_type") != "standings":
            continue
        payload = record.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        team = payload.get("team")
        if isinstance(team, str) and team.strip():
            out[_slug(team)] = payload
    return out


def _discipline_by_team(batch: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for record in batch.get("records", []):
        if not isinstance(record, dict) or record.get("record_type") != "discipline_team":
            continue
        payload = record.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        team = payload.get("team")
        if isinstance(team, str) and team.strip():
            out[_slug(team)] = payload
    return out


def _results_by_team(batch: dict[str, Any]) -> dict[str, list[TeamResult]]:
    out: dict[str, list[TeamResult]] = {}
    for index, record in enumerate(batch.get("records", [])):
        if not isinstance(record, dict) or record.get("record_type") != "result":
            continue
        payload = record.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        home = payload.get("home_team")
        away = payload.get("away_team")
        hg = payload.get("home_goals")
        ag = payload.get("away_goals")
        if not (isinstance(home, str) and isinstance(away, str) and isinstance(hg, int) and isinstance(ag, int)):
            continue
        home_key = _slug(home)
        away_key = _slug(away)
        home_points, away_points = _points(hg, ag)
        home_result = TeamResult(
            index=index,
            team=home,
            opponent=away,
            is_home=True,
            points=home_points,
            goal_diff=hg - ag,
            match_date=payload.get("match_date") if isinstance(payload.get("match_date"), str) else None,
        )
        away_result = TeamResult(
            index=index,
            team=away,
            opponent=home,
            is_home=False,
            points=away_points,
            goal_diff=ag - hg,
            match_date=payload.get("match_date") if isinstance(payload.get("match_date"), str) else None,
        )
        out.setdefault(home_key, []).append(home_result)
        out.setdefault(away_key, []).append(away_result)
    for team_results in out.values():
        team_results.sort(key=lambda item: (item.match_date or "", item.index))
    return out


def _standings_axis(
    *,
    axis_id: str,
    label: str,
    team_key: str,
    values: dict[str, float],
    invert: bool,
    raw_label: str,
    source: dict[str, Any],
    row: dict[str, Any],
) -> dict[str, Any]:
    raw = values.get(team_key)
    if raw is None:
        return _missing_axis(axis_id, label, source, "classificacao sem jogos suficientes")
    value = _scale_minmax(raw, list(values.values()), invert=invert)
    return _axis(
        axis_id=axis_id,
        label=label,
        base=value,
        atual=value,
        status="ok",
        qualidade=_source_quality(source),
        source=source,
        janela={"tipo": "temporada", "jogos": row.get("played")},
        valor_bruto={raw_label: round(raw, 4)},
    )


def _form_axis(team_key: str, results: list[TeamResult], source: dict[str, Any]) -> dict[str, Any]:
    if len(results) < 3:
        return _missing_axis("forma_recente", "Forma recente", source, "menos de 3 resultados oficiais no lote")
    recent = results[-5:]
    value = round((sum(item.points for item in recent) / (len(recent) * 3)) * 100, 2)
    status = "ok" if len(recent) >= 5 else "baixa_amostra"
    quality = _source_quality(source) if status == "ok" else min(_source_quality(source), 2.5)
    return _axis(
        axis_id="forma_recente",
        label="Forma recente",
        base=value,
        atual=value,
        status=status,
        qualidade=quality,
        source=source,
        janela={"tipo": "ultimos_resultados", "jogos": len(recent)},
        valor_bruto={"pontos": sum(item.points for item in recent), "max_pontos": len(recent) * 3},
    )


def _consistency_axis(team_key: str, results: list[TeamResult], source: dict[str, Any]) -> dict[str, Any]:
    if len(results) < 5:
        return _missing_axis("consistencia", "Consistencia", source, "menos de 5 resultados oficiais no lote")
    recent = results[-8:]
    goal_diffs = [item.goal_diff for item in recent]
    stdev = _stdev(goal_diffs)
    value = round(max(0.0, 100.0 - min(stdev / 3.0, 1.0) * 100.0), 2)
    return _axis(
        axis_id="consistencia",
        label="Consistencia",
        base=value,
        atual=value,
        status="ok",
        qualidade=_source_quality(source),
        source=source,
        janela={"tipo": "ultimos_resultados", "jogos": len(recent)},
        valor_bruto={"desvio_saldo_gols": round(stdev, 4)},
    )


def _context_axis(
    team_key: str,
    results: list[TeamResult],
    source: dict[str, Any],
    *,
    contexto: str,
) -> dict[str, Any]:
    if contexto == "casa":
        scoped = [item for item in results if item.is_home]
        label_context = "casa"
    elif contexto == "fora":
        scoped = [item for item in results if not item.is_home]
        label_context = "fora"
    else:
        scoped = results
        label_context = "geral"

    if len(scoped) < 3:
        return _missing_axis(
            "contexto_casa_fora",
            "Contexto casa/fora",
            source,
            f"menos de 3 resultados oficiais no contexto {label_context}",
        )
    value = round((sum(item.points for item in scoped) / (len(scoped) * 3)) * 100, 2)
    status = "ok" if len(scoped) >= 5 else "baixa_amostra"
    quality = _source_quality(source) if status == "ok" else min(_source_quality(source), 2.5)
    return _axis(
        axis_id="contexto_casa_fora",
        label="Contexto casa/fora",
        base=value,
        atual=value,
        status=status,
        qualidade=quality,
        source=source,
        janela={"tipo": label_context, "jogos": len(scoped)},
        valor_bruto={"pontos": sum(item.points for item in scoped), "max_pontos": len(scoped) * 3},
    )


def _discipline_axis(
    team_key: str,
    values: dict[str, float],
    source: dict[str, Any],
    row: dict[str, Any],
) -> dict[str, Any]:
    raw = values.get(team_key)
    if raw is None:
        return _missing_axis("controle_disciplinar", "Controle disciplinar", source, "CA/CV nao encontrados")
    value = _scale_minmax(raw, list(values.values()), invert=True)
    return _axis(
        axis_id="controle_disciplinar",
        label="Controle disciplinar",
        base=value,
        atual=value,
        status="ok",
        qualidade=_source_quality(source),
        source=source,
        janela={"tipo": "temporada", "jogos": row.get("played")},
        valor_bruto={"cartoes_ponderados_por_jogo": round(raw, 4)},
    )


def _axis(
    *,
    axis_id: str,
    label: str,
    base: float | None,
    atual: float | None,
    status: str,
    qualidade: float,
    source: dict[str, Any],
    janela: dict[str, Any],
    valor_bruto: dict[str, Any] | None = None,
    motivo_ausencia: str | None = None,
) -> dict[str, Any]:
    return {
        "id": axis_id,
        "label": label,
        "base": base,
        "atual": atual,
        "delta": None if base is None or atual is None else round(atual - base, 2),
        "qualidade": qualidade,
        "status": status,
        "janela": janela,
        "referencia": {"liga": None, "temporada": None},
        "fontes": [_source_ref(source)],
        "valor_bruto": valor_bruto or {},
        "modificadores": [],
        "motivo_ausencia": motivo_ausencia,
    }


def _missing_axis(axis_id: str, label: str, source: dict[str, Any], reason: str) -> dict[str, Any]:
    return _axis(
        axis_id=axis_id,
        label=label,
        base=None,
        atual=None,
        status="dado_ausente",
        qualidade=0,
        source=source,
        janela={"tipo": "indisponivel", "jogos": 0},
        motivo_ausencia=reason,
    )


def _per_played_metric(standings: dict[str, dict[str, Any]], field: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for team_key, row in standings.items():
        played = row.get("played")
        value = row.get(field)
        if isinstance(played, int) and played > 0 and isinstance(value, int):
            out[team_key] = value / played
    return out


def _discipline_metric(
    standings: dict[str, dict[str, Any]],
    discipline: dict[str, dict[str, Any]],
) -> dict[str, float]:
    out: dict[str, float] = {}
    for team_key, row in standings.items():
        played = row.get("played")
        cards = discipline.get(team_key) or row
        yellow = cards.get("yellow_cards")
        red = cards.get("red_cards")
        if isinstance(played, int) and played > 0 and isinstance(yellow, int) and isinstance(red, int):
            out[team_key] = (yellow + 3 * red) / played
    return out


def _scale_minmax(value: float, values: list[float], *, invert: bool) -> float:
    clean = [item for item in values if isinstance(item, (int, float)) and not isinstance(item, bool)]
    if not clean:
        return 50.0
    lo = min(clean)
    hi = max(clean)
    if math.isclose(lo, hi):
        score = 50.0
    else:
        score = ((value - lo) / (hi - lo)) * 100.0
    if invert:
        score = 100.0 - score
    return round(max(0.0, min(100.0, score)), 2)


def _points(home_goals: int, away_goals: int) -> tuple[int, int]:
    if home_goals > away_goals:
        return 3, 0
    if home_goals < away_goals:
        return 0, 3
    return 1, 1


def _stdev(values: list[int]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((item - mean) ** 2 for item in values) / len(values))


def _source_quality(source: dict[str, Any]) -> float:
    quality = source.get("quality_score")
    if isinstance(quality, (int, float)) and not isinstance(quality, bool):
        return float(quality)
    return 0.0


def _source_ref(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": source.get("source_id"),
        "source_url": source.get("source_url"),
        "fetched_at": source.get("fetched_at"),
        "quality_score": source.get("quality_score"),
        "status_fonte": source.get("status_fonte"),
    }


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(char for char in normalized if not unicodedata.combining(char)).lower()
    out = []
    previous_dash = False
    for char in ascii_value:
        if char.isalnum():
            out.append(char)
            previous_dash = False
        elif not previous_dash:
            out.append("-")
            previous_dash = True
    return "".join(out).strip("-")

