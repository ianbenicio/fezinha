"""Ingestão via ge.globo.com (grátis) → Supabase.

Extrai o JSON embutido na página do Brasileirão (`const classificacao = {...}`
dentro de <script id="scriptReact">). Técnica auditada do projeto público
laravel-scraper-globo (limpo). Sem API, sem custo.

Coleta:
- Classificação: posição, pontos, jogos, V/E/D, gols, saldo, forma (últimos 5), escudo.
- Jogos da rodada atual: data/hora reais, placar (se houver) — pega as datas do
  returno que a CBF ainda não detalhou.

NÃO traz xG (ge não publica). Para xG, só fonte paga.

Requer env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
Uso:
  python -m engine.ingestion.ge_globo classificacao  # tabela + escudos + forma
  python -m engine.ingestion.ge_globo jogos          # jogos da rodada atual (datas)
  python -m engine.ingestion.ge_globo all
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from typing import Any

import httpx

URLS = {
    "brasileirao_serie_a": "https://ge.globo.com/futebol/brasileirao-serie-a/",
    "brasileirao_serie_b": "https://ge.globo.com/futebol/brasileirao-serie-b/",
}
SOURCE_ID = "ge_globo"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def _sb():
    from supabase import create_client
    url = os.getenv("SUPABASE_URL"); srk = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and srk):
        sys.exit("ERRO: defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY no .env")
    return create_client(url, srk)


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return "".join(c for c in s if c.isalnum())


# aliases nome_popular (ge) -> nosso nome normalizado
ALIAS = {
    "bragantino": "redbullbragantino", "athleticopr": "athleticoparanaense",
    "atleticomg": "atleticomineiro", "atleticogo": "atleticogoianiense",
}


def buscar(liga: str) -> dict[str, Any]:
    r = httpx.get(URLS[liga], headers={"User-Agent": UA}, timeout=30, follow_redirects=True)
    r.raise_for_status()
    m = re.search(r"const classificacao = (\{.*?\});", r.text, re.DOTALL)
    if not m:
        raise RuntimeError(f"script de classificação não encontrado ({liga})")
    return json.loads(m.group(1))


def _mapa_times(sb, liga: str) -> dict[str, int]:
    """nome normalizado -> nosso team_id."""
    rows = sb.table("teams").select("id, nome").eq("liga", liga).execute().data
    return {_norm(t["nome"]): t["id"] for t in rows}


def _resolver(nome_ge: str, mapa: dict[str, int]) -> int | None:
    n = _norm(nome_ge)
    n = ALIAS.get(n, n)
    return mapa.get(n)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _with_source_meta(car: dict[str, Any], liga: str, fields: list[str], fetched_at: str) -> dict[str, Any]:
    fontes = car.get("_fontes")
    if not isinstance(fontes, dict):
        fontes = {}
    fontes[SOURCE_ID] = {
        "source_id": SOURCE_ID,
        "source_url": URLS[liga],
        "fetched_at": fetched_at,
        "quality_score": 3,
        "status_fonte": "ativo",
        "ingestion_method": "scraper_html_json_embutido",
        "fields": fields,
    }
    car["_fontes"] = fontes
    return car


def sync_classificacao(sb, liga: str) -> None:
    d = buscar(liga)
    fetched_at = _utc_now()
    mapa = _mapa_times(sb, liga)
    atualizados = 0
    for t in d.get("classificacao", []):
        tid = _resolver(t["nome_popular"], mapa)
        if not tid:
            print(f"  [sem match] {t['nome_popular']}")
            continue
        # mescla dados de tabela nas caracteristicas (preserva ataque/defesa)
        atual = sb.table("teams").select("caracteristicas").eq("id", tid).single().execute().data
        car = (atual or {}).get("caracteristicas") or {}
        car.update({
            "posicao": t["ordem"], "pontos": t["pontos"], "jogos": t["jogos"],
            "vitorias": t["vitorias"], "empates": t["empates"], "derrotas": t["derrotas"],
            "gols_pro": t["gols_pro"], "gols_contra": t["gols_contra"],
            "saldo_gols": t["saldo_gols"], "aproveitamento": t["aproveitamento"],
            "forma": t.get("ultimos_jogos", []),
            "faixa_cor": t.get("faixa_classificacao_cor"),
        })
        car = _with_source_meta(
            car,
            liga,
            [
                "classificacao",
                "pontos",
                "jogos",
                "vitorias",
                "empates",
                "derrotas",
                "gols",
                "forma",
                "escudo",
            ],
            fetched_at,
        )
        sb.table("teams").update({
            "escudo_url": t.get("escudo"), "caracteristicas": car,
        }).eq("id", tid).execute()
        atualizados += 1
    print(f"  {liga}: classificação/escudos atualizados em {atualizados} times")


def sync_jogos(sb, liga: str) -> None:
    d = buscar(liga)
    mapa = _mapa_times(sb, liga)
    rodada = (d.get("rodada") or {}).get("atual")
    total = 0
    for j in d.get("lista_jogos", []):
        eq = j["equipes"]
        h = _resolver(eq["mandante"]["nome_popular"], mapa)
        a = _resolver(eq["visitante"]["nome_popular"], mapa)
        if not (h and a):
            continue
        data = j.get("data_realizacao")
        pm, pv = j.get("placar_oficial_mandante"), j.get("placar_oficial_visitante")
        encerrado = pm is not None and pv is not None
        row = {
            "data_hora": data, "rodada": rodada,
            "status": "encerrado" if encerrado else "agendado",
            "placar_casa": pm, "placar_fora": pv,
        }
        # casa por (liga, mandante, visitante, rodada) — atualiza o jogo existente
        ex = (sb.table("matches").select("id")
              .eq("liga", liga).eq("home_team_id", h).eq("away_team_id", a)
              .eq("rodada", rodada).execute().data)
        if ex:
            sb.table("matches").update(row).eq("id", ex[0]["id"]).execute()
        else:
            sb.table("matches").insert({**row, "liga": liga,
                                        "home_team_id": h, "away_team_id": a}).execute()
        total += 1
    print(f"  {liga}: {total} jogos da rodada {rodada} sincronizados")


def sync_noticias(sb, liga: str, max_itens: int = 10) -> None:
    r = httpx.get(URLS[liga], headers={"User-Agent": UA}, timeout=30, follow_redirects=True)
    r.raise_for_status()
    pares = re.findall(
        r'<a[^>]+href="(https://ge\.globo\.com/[^"]*?/noticia/[^"]+\.ghtml)"[^>]*>(.*?)</a>',
        r.text, re.DOTALL)
    vistos = set(); total = 0
    for url, txt in pares:
        titulo = re.sub(r"<[^>]+>", " ", txt)
        titulo = re.sub(r"\s+", " ", titulo).strip().replace("&quot;", '"')
        if len(titulo) < 20 or url in vistos:
            continue
        vistos.add(url)
        d = re.search(r"/noticia/(\d{4})/(\d{2})/(\d{2})/", url)
        data = f"{d.group(1)}-{d.group(2)}-{d.group(3)}" if d else None
        ex = sb.table("news").select("id").eq("url", url).execute().data
        if not ex:
            sb.table("news").insert({
                "titulo": titulo[:200], "url": url, "fonte": "ge.globo",
                "liga": liga, "publicado_em": data,
            }).execute()
            total += 1
        if len(vistos) >= max_itens:
            break
    print(f"  {liga}: {total} notícias novas")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    sb = _sb()
    if cmd in ("classificacao", "all"):
        for liga in URLS:
            try: sync_classificacao(sb, liga)
            except Exception as e: print(f"  erro {liga}: {e}")
    if cmd in ("jogos", "all"):
        for liga in URLS:
            try: sync_jogos(sb, liga)
            except Exception as e: print(f"  erro {liga}: {e}")
    if cmd in ("noticias", "all"):
        for liga in URLS:
            try: sync_noticias(sb, liga)
            except Exception as e: print(f"  erro {liga}: {e}")
    if cmd not in ("classificacao", "jogos", "noticias", "all"):
        print(__doc__)


if __name__ == "__main__":
    main()
