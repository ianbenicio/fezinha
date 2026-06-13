"""Ingestão via API-Football (api-sports.io) → Supabase.

Cobre: times (mapa api_team_id), jogos/resultados, estatísticas de jogo
(xG, posse, escanteios, cartões), estatísticas de jogador (xG+xA, minutos),
lesões/suspensões.

Roda como script (cron). Requer env:
  API_FOOTBALL_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

Uso:
  python -m engine.ingestion.api_football teams      # mapeia times (1x por temporada)
  python -m engine.ingestion.api_football fixtures   # jogos + resultados
  python -m engine.ingestion.api_football stats       # estatísticas por jogo
  python -m engine.ingestion.api_football players      # jogadores + stats
  python -m engine.ingestion.api_football injuries     # lesões/suspensões
  python -m engine.ingestion.api_football all          # tudo (cuidado com cota)

Free tier: 100 req/dia. O script loga o consumo e respeita rate-limit.
"""
from __future__ import annotations

import os
import sys
import time
from typing import Any

import httpx

BASE = "https://v3.football.api-sports.io"
TEMPORADA = 2026
# IDs da API-Football para o Brasileirão
LIGAS = {"brasileirao_serie_a": 71, "brasileirao_serie_b": 72}
RATE_DELAY = 6.5  # s entre chamadas (~9/min, seguro no free tier)


def _key() -> str:
    k = os.getenv("API_FOOTBALL_KEY")
    if not k:
        sys.exit("ERRO: defina API_FOOTBALL_KEY no .env")
    return k


def _sb():
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    srk = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and srk):
        sys.exit("ERRO: defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY no .env")
    return create_client(url, srk)


def _get(client: httpx.Client, path: str, params: dict) -> list[dict[str, Any]]:
    """GET com rate-limit e tratamento de cota."""
    r = client.get(f"{BASE}{path}", params=params, timeout=30)
    rem = r.headers.get("x-ratelimit-requests-remaining")
    if rem is not None:
        print(f"    [cota restante hoje: {rem}]")
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        print(f"    aviso API: {data['errors']}")
    time.sleep(RATE_DELAY)
    return data.get("response", [])


def _norm(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return "".join(c for c in s if c.isalnum())


# ── 1. TIMES: mapeia api_team_id casando por nome ───────
def sync_teams(client: httpx.Client, sb) -> dict[int, int]:
    """Retorna {api_team_id: nosso team_id}. Grava api_team_id em teams."""
    nossos = sb.table("teams").select("id, nome, slug, liga, api_team_id").execute().data
    by_norm = {_norm(t["nome"]): t for t in nossos}
    # alguns aliases comuns API → nosso nome
    alias = {"redbullbragantino": "bragantino", "athleticoparanaense": "athleticopr",
             "atleticomineiro": "atleticomg", "atleticogoianiense": "atleticogo"}
    mapa: dict[int, int] = {}
    for liga, lid in LIGAS.items():
        resp = _get(client, "/teams", {"league": lid, "season": TEMPORADA})
        for item in resp:
            api = item["team"]
            nome_norm = _norm(api["name"])
            nome_norm = alias.get(nome_norm, nome_norm)
            nosso = by_norm.get(nome_norm)
            if not nosso:
                print(f"    [sem match] API '{api['name']}' (liga {liga})")
                continue
            sb.table("teams").update({"api_team_id": api["id"]}).eq("id", nosso["id"]).execute()
            mapa[api["id"]] = nosso["id"]
    print(f"  times mapeados: {len(mapa)}")
    return mapa


def _carrega_mapa_times(sb) -> dict[int, int]:
    rows = sb.table("teams").select("id, api_team_id").not_.is_("api_team_id", "null").execute().data
    return {r["api_team_id"]: r["id"] for r in rows}


# ── 2. JOGOS / RESULTADOS ───────────────────────────────
def sync_fixtures(client: httpx.Client, sb) -> None:
    mapa = _carrega_mapa_times(sb)
    if not mapa:
        sys.exit("ERRO: rode 'teams' primeiro (mapa api_team_id vazio)")
    total = 0
    for liga, lid in LIGAS.items():
        resp = _get(client, "/fixtures", {"league": lid, "season": TEMPORADA})
        for fx in resp:
            f = fx["fixture"]; g = fx["goals"]; tm = fx["teams"]
            h = mapa.get(tm["home"]["id"]); a = mapa.get(tm["away"]["id"])
            if not (h and a):
                continue
            st = f["status"]["short"]
            status = "encerrado" if st in ("FT", "AET", "PEN") else (
                "ao_vivo" if st in ("1H", "2H", "HT", "ET") else
                "adiado" if st in ("PST", "CANC") else "agendado")
            row = {
                "liga": liga, "home_team_id": h, "away_team_id": a,
                "data_hora": f["date"], "rodada": _rodada(fx),
                "status": status, "api_fixture_id": f["id"],
                "arbitro": f.get("referee"),
                "placar_casa": g["home"], "placar_fora": g["away"],
            }
            # upsert por api_fixture_id
            ex = sb.table("matches").select("id").eq("api_fixture_id", f["id"]).execute().data
            if ex:
                sb.table("matches").update(row).eq("id", ex[0]["id"]).execute()
            else:
                sb.table("matches").insert(row).execute()
            total += 1
    print(f"  jogos sincronizados: {total}")


def _rodada(fx: dict) -> int | None:
    rnd = fx.get("league", {}).get("round", "")
    digs = "".join(c for c in rnd if c.isdigit())
    return int(digs) if digs else None


# ── 3. ESTATÍSTICAS POR JOGO ────────────────────────────
def sync_match_stats(client: httpx.Client, sb, limite: int = 15) -> None:
    """Stats dos jogos encerrados sem stats ainda. Limite por causa da cota."""
    mapa = _carrega_mapa_times(sb)
    jogos = (sb.table("matches")
             .select("id, api_fixture_id, home_team_id, away_team_id")
             .eq("status", "encerrado").not_.is_("api_fixture_id", "null")
             .execute().data)
    com_stats = {r["match_id"] for r in sb.table("match_stats").select("match_id").execute().data}
    pendentes = [j for j in jogos if j["id"] not in com_stats][:limite]
    print(f"  jogos pendentes de stats: {len(pendentes)} (processando {len(pendentes)})")
    for j in pendentes:
        resp = _get(client, "/fixtures/statistics", {"fixture": j["api_fixture_id"]})
        for time_stats in resp:
            tid = mapa.get(time_stats["team"]["id"])
            if not tid:
                continue
            s = {x["type"]: x["value"] for x in time_stats["statistics"]}
            row = {
                "match_id": j["id"], "team_id": tid,
                "xg": _num(s.get("expected_goals")),
                "posse": _pct(s.get("Ball Possession")),
                "escanteios": _int(s.get("Corner Kicks")),
                "finalizacoes": _int(s.get("Total Shots")),
                "finalizacoes_no_gol": _int(s.get("Shots on Goal")),
                "faltas": _int(s.get("Fouls")),
                "cartoes_amarelos": _int(s.get("Yellow Cards")),
                "cartoes_vermelhos": _int(s.get("Red Cards")),
            }
            _upsert(sb, "match_stats", row, ["match_id", "team_id"])
    print("  stats de jogo OK")


# ── 4. JOGADORES + STATS ────────────────────────────────
def sync_players(client: httpx.Client, sb, max_paginas: int = 8) -> None:
    mapa = _carrega_mapa_times(sb)
    total = 0
    for liga, lid in LIGAS.items():
        pagina = 1
        while pagina <= max_paginas:
            resp = _get(client, "/players", {"league": lid, "season": TEMPORADA, "page": pagina})
            if not resp:
                break
            for item in resp:
                p = item["player"]; stt = (item.get("statistics") or [{}])[0]
                tid = mapa.get(stt.get("team", {}).get("id"))
                if not tid:
                    continue
                pid = _upsert_player(sb, p, tid, stt)
                if pid:
                    _gravar_player_stats(sb, pid, stt)
                    total += 1
            pagina += 1
    print(f"  jogadores sincronizados: {total}")


def _upsert_player(sb, p: dict, team_id: int, stt: dict) -> int | None:
    ex = sb.table("players").select("id").eq("api_player_id", p["id"]).execute().data
    row = {
        "team_id": team_id, "nome": p["name"],
        "posicao": stt.get("games", {}).get("position"),
        "api_player_id": p["id"],
    }
    if ex:
        sb.table("players").update(row).eq("id", ex[0]["id"]).execute()
        return ex[0]["id"]
    ins = sb.table("players").insert(row).execute().data
    return ins[0]["id"] if ins else None


def _gravar_player_stats(sb, player_id: int, stt: dict) -> None:
    g = stt.get("games", {}); goals = stt.get("goals", {}); cards = stt.get("cards", {})
    row = {
        "player_id": player_id, "temporada": TEMPORADA,
        "jogos": g.get("appearences") or 0, "minutos": g.get("minutes") or 0,
        "gols": goals.get("total") or 0, "assistencias": goals.get("assists") or 0,
        "xg": _num(stt.get("expected", {}).get("goals")) or 0,
        "xa": _num(stt.get("expected", {}).get("assists")) or 0,
        "cartoes_amarelos": cards.get("yellow") or 0,
        "cartoes_vermelhos": cards.get("red") or 0,
    }
    _upsert(sb, "player_stats", row, ["player_id", "temporada"])


# ── 5. LESÕES / SUSPENSÕES ──────────────────────────────
def sync_injuries(client: httpx.Client, sb) -> None:
    total = 0
    for liga, lid in LIGAS.items():
        resp = _get(client, "/injuries", {"league": lid, "season": TEMPORADA})
        for item in resp:
            api_pid = item["player"]["id"]
            ours = sb.table("players").select("id").eq("api_player_id", api_pid).execute().data
            if not ours:
                continue
            tipo = (item["player"].get("type") or "").lower()
            status = "suspenso" if "suspend" in tipo else ("duvida" if "questionable" in tipo else "lesionado")
            _upsert(sb, "player_status", {
                "player_id": ours[0]["id"], "status": status,
                "motivo": item["player"].get("reason"),
            }, ["player_id"])
            total += 1
    print(f"  status de jogadores atualizados: {total}")


# ── helpers ─────────────────────────────────────────────
def _num(v):
    try: return float(str(v).replace("%", "")) if v not in (None, "") else None
    except (ValueError, TypeError): return None

def _int(v):
    try: return int(v) if v not in (None, "") else None
    except (ValueError, TypeError): return None

def _pct(v):
    return _int(str(v).replace("%", "")) if v else None

def _upsert(sb, tabela: str, row: dict, chave: list[str]):
    q = sb.table(tabela).select("id")
    for k in chave:
        q = q.eq(k, row[k])
    ex = q.execute().data
    if ex:
        sb.table(tabela).update(row).eq("id", ex[0]["id"]).execute()
    else:
        sb.table(tabela).insert(row).execute()


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    client = httpx.Client(headers={"x-apisports-key": _key()})
    sb = _sb()
    acoes = {
        "teams": lambda: sync_teams(client, sb),
        "fixtures": lambda: sync_fixtures(client, sb),
        "stats": lambda: sync_match_stats(client, sb),
        "players": lambda: sync_players(client, sb),
        "injuries": lambda: sync_injuries(client, sb),
    }
    if cmd == "all":
        for nome, fn in acoes.items():
            print(f"== {nome} =="); fn()
    elif cmd in acoes:
        print(f"== {cmd} =="); acoes[cmd]()
    else:
        print(__doc__)
    client.close()


if __name__ == "__main__":
    main()
