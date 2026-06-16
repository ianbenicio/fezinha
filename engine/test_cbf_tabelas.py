"""Tests for CBF HTML parser.

Run: python -m engine.test_cbf_tabelas
"""
from __future__ import annotations

from .ingestion.cbf_tabelas import build_manual_batch, parse_matches_html, parse_standings_html
from .ingestion.manual_source_batch import validate_batch


HTML = """
<table>
  <thead>
    <tr>
      <th>Classifica\u00e7\u00e3o</th><th>PTSPontos</th><th>JJogos</th><th>VVit\u00f3rias</th>
      <th>EEmpates</th><th>DDerrotas</th><th>GPGols Pr\u00f3s</th><th>GCGols Contras</th>
      <th>SGSaldos de Gols</th><th>CACart\u00f5es Amarelos</th><th>CVCart\u00f5es Vermelhos</th>
      <th>%Aproveitamento</th><th>Recentes</th><th>Pr\u00f3xPr\u00f3ximo</th>
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
<div class="styles_gameCardContainer__qbcs6 styles_card__Wpuug">
  <div class="styles_score__M9df8">
    <div><a><strong title="Atletico Goianiense Saf">Atl</strong></a><span class="styles_gol__wQ4q9">3</span></div>
    <span>X</span>
    <div><a><strong title="Crb">Crb</strong></a><span class="styles_gol__wQ4q9">3</span></div>
  </div>
  <div class="styles_informations__K0gXK">
    <span class="styles_numberGame__dZ2sG">Jogo 126</span>
    <p> 12/06/2026 - 19:00<br> Goiania - GO<br>Antonio Accioly </p>
    <a href="https://www.cbf.com.br/futebol-brasileiro/jogos/campeonato-brasileiro/serie-b/2026/atletico-x-crb/833007">Documentos do jogo</a>
  </div>
</div>
<div class="styles_gameCardContainer__qbcs6 styles_card__Wpuug">
  <div class="styles_score__M9df8">
    <div><a><strong title="Sao Bernardo">Sao</strong></a></div>
    <span>X</span>
    <div><a><strong title="Sport Recife">Spo</strong></a></div>
  </div>
  <div class="styles_informations__K0gXK">
    <span class="styles_numberGame__dZ2sG">Jogo 122</span>
    <p> 20/06/2026 - 11:00<br> Sao Bernardo do Campo - SP<br>1 de Maio </p>
    <a href="https://www.cbf.com.br/futebol-brasileiro/jogos/campeonato-brasileiro/serie-b/2026/sao-bernardo-x-sport-recife/833003">Documentos do jogo</a>
  </div>
</div>
"""


def test_parse_standings_html():
    rows = parse_standings_html(HTML)
    assert len(rows) == 2
    assert rows[0].team == "Sao Bernardo"
    assert rows[0].yellow_cards == 30
    assert rows[1].red_cards == 4


def test_parse_matches_html():
    matches = parse_matches_html(HTML)
    assert len(matches) == 2
    assert matches[0].home_team == "Atletico Goianiense Saf"
    assert matches[0].home_goals == 3
    assert matches[0].away_goals == 3
    assert matches[0].match_date == "2026-06-12"
    assert matches[1].home_goals is None
    assert matches[1].stadium == "1 de Maio"


def test_build_batch_validates():
    rows = parse_standings_html(HTML)
    matches = parse_matches_html(HTML)
    batch = build_manual_batch(
        rows,
        liga="brasileirao_serie_b",
        season=2026,
        round_number=13,
        source_url="https://www.cbf.com.br/futebol-brasileiro/tabelas/campeonato-brasileiro/serie-b/2026",
        fetched_at="2026-06-15T11:27:00-03:00",
        snapshot_path="F:/snapshot.html",
        raw_payload_hash="sha256:abc",
        matches=matches,
    )
    report = validate_batch(batch)
    assert not report.errors
    assert len(batch["records"]) == 6
    assert batch["records"][1]["record_type"] == "discipline_team"
    assert batch["records"][4]["record_type"] == "result"
    assert batch["records"][5]["record_type"] == "fixture"


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

