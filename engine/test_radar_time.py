"""Tests for explanatory team radar payloads.

Run: python -m engine.test_radar_time
"""
from __future__ import annotations

from .radar_time import build_radar_for_team, build_radars_from_manual_batch


def _record(record_id: str, record_type: str, natural_key: str, payload: dict) -> dict:
    return {
        "record_id": record_id,
        "record_type": record_type,
        "natural_key": natural_key,
        "status": "ok",
        "quality_score": 4,
        "evidence": {"quote": record_id, "page": None, "line": None, "selector": None, "table": "test"},
        "payload": payload,
    }


def _batch() -> dict:
    base = {
        "schema_version": "manual_source_batch_v0",
        "batch_id": "radar-test",
        "created_at": "2026-06-15T12:00:00-03:00",
        "created_by": "test",
        "notes": None,
        "source": {
            "source_id": "cbf_tabelas",
            "source_name": "CBF - Tabelas",
            "source_url": "https://www.cbf.com.br/",
            "source_type": "oficial_primaria",
            "fetched_at": "2026-06-15T12:00:00-03:00",
            "quality_score": 4,
            "status_fonte": "ativo",
            "ingestion_method": "scraper_html",
            "source_snapshot_path": "F:/snapshot.html",
            "raw_payload_hash": "sha256:test",
            "extraction_tool": "test",
        },
        "records": [],
    }
    standings = [
        ("Alpha FC", 1, 20, 10, 6, 2, 2, 22, 10, 12, 20, 1, 66),
        ("Beta FC", 2, 14, 10, 4, 2, 4, 12, 14, -2, 30, 3, 46),
        ("Gamma FC", 3, 10, 10, 3, 1, 6, 8, 18, -10, 25, 2, 33),
    ]
    for team, pos, pts, played, wins, draws, losses, gf, ga, gd, yellow, red, pct in standings:
        slug = team.lower().replace(" ", "-")
        payload = {
            "competition": "brasileirao_serie_a",
            "season": 2026,
            "round": 10,
            "position": pos,
            "team": team,
            "points": pts,
            "played": played,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_for": gf,
            "goals_against": ga,
            "goal_difference": gd,
            "yellow_cards": yellow,
            "red_cards": red,
            "points_percentage": pct,
        }
        base["records"].append(_record(f"standings-{slug}", "standings", f"liga:2026:10:{slug}:standings", payload))
        base["records"].append(
            _record(
                f"discipline-{slug}",
                "discipline_team",
                f"liga:2026:10:{slug}:discipline_team",
                {
                    "competition": "brasileirao_serie_a",
                    "season": 2026,
                    "round": 10,
                    "team": team,
                    "yellow_cards": yellow,
                    "red_cards": red,
                },
            )
        )

    results = [
        ("Alpha FC", "Beta FC", 2, 0, "2026-05-01"),
        ("Gamma FC", "Alpha FC", 1, 1, "2026-05-05"),
        ("Alpha FC", "Gamma FC", 3, 1, "2026-05-10"),
        ("Beta FC", "Alpha FC", 0, 1, "2026-05-15"),
        ("Alpha FC", "Beta FC", 1, 1, "2026-05-20"),
    ]
    for index, (home, away, hg, ag, day) in enumerate(results):
        base["records"].append(
            _record(
                f"result-{index}",
                "result",
                f"liga:2026:{index}:{home}:{away}:result",
                {
                    "competition": "brasileirao_serie_a",
                    "season": 2026,
                    "round": index + 1,
                    "home_team": home,
                    "away_team": away,
                    "home_goals": hg,
                    "away_goals": ag,
                    "status": "finished",
                    "match_date": day,
                },
            )
        )
    return base


def test_build_radars_from_manual_batch():
    radars = build_radars_from_manual_batch(_batch())
    alpha = radars["alpha-fc"]
    assert alpha["schema_version"] == "radar_time_v0"
    assert alpha["team"]["id"] is None
    assert alpha["team"]["slug"] == "alpha-fc"
    assert alpha["meta"]["entra_no_agregador"] is False
    axes = {axis["id"]: axis for axis in alpha["eixos"]}
    assert axes["forca_ofensiva"]["status"] == "ok"
    assert axes["forca_ofensiva"]["referencia"] == {"liga": "brasileirao_serie_a", "temporada": 2026}
    assert axes["controle_disciplinar"]["status"] == "ok"
    assert axes["forma_recente"]["status"] == "ok"
    assert axes["consistencia"]["status"] == "ok"


def test_context_axis_can_be_home_specific():
    alpha = build_radar_for_team(_batch(), "Alpha FC", contexto="casa")
    axes = {axis["id"]: axis for axis in alpha["eixos"]}
    assert axes["contexto_casa_fora"]["status"] == "baixa_amostra"
    assert axes["contexto_casa_fora"]["janela"]["tipo"] == "casa"


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
