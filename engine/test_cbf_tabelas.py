"""Tests for CBF HTML standings parser.

Run: python -m engine.test_cbf_tabelas
"""
from __future__ import annotations

from .ingestion.cbf_tabelas import build_manual_batch, parse_standings_html
from .ingestion.manual_source_batch import validate_batch


HTML = """
<table>
  <thead>
    <tr>
      <th>Classificação</th><th>PTSPontos</th><th>JJogos</th><th>VVitórias</th>
      <th>EEmpates</th><th>DDerrotas</th><th>GPGols Prós</th><th>GCGols Contras</th>
      <th>SGSaldos de Gols</th><th>CACartões Amarelos</th><th>CVCartões Vermelhos</th>
      <th>%Aproveitamento</th><th>Recentes</th><th>PróxPróximo</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1Sao Bernardo</td><td>25</td><td>13</td><td>7</td><td>4</td><td>2</td>
      <td>20</td><td>10</td><td>10</td><td>30</td><td>1</td><td>64</td><td></td><td></td>
    </tr>
    <tr>
      <td>2Vila Nova</td><td>25</td><td>13</td><td>7</td><td>4</td><td>2</td>
      <td>18</td><td>12</td><td>6</td><td>45</td><td>4</td><td>64</td><td></td><td></td>
    </tr>
  </tbody>
</table>
"""


def test_parse_standings_html():
    rows = parse_standings_html(HTML)
    assert len(rows) == 2
    assert rows[0].team == "Sao Bernardo"
    assert rows[0].yellow_cards == 30
    assert rows[1].red_cards == 4


def test_build_batch_validates():
    rows = parse_standings_html(HTML)
    batch = build_manual_batch(
        rows,
        liga="brasileirao_serie_b",
        season=2026,
        round_number=13,
        source_url="https://www.cbf.com.br/futebol-brasileiro/tabelas/campeonato-brasileiro/serie-b/2026",
        fetched_at="2026-06-15T11:27:00-03:00",
        snapshot_path="F:/snapshot.html",
        raw_payload_hash="sha256:abc",
    )
    report = validate_batch(batch)
    assert not report.errors
    assert len(batch["records"]) == 4
    assert batch["records"][1]["record_type"] == "discipline_team"


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

