"""Parser da Tabela Detalhada oficial da CBF (PDF) — Brasileirão Série A.

Extrai de cada jogo: rodada, data, hora, mandante, visitante, placar (se houver),
estádio. Mapeia nomes do PDF para os slugs do catálogo. Jogos com placar
alimentam a força dos times (ataque/defesa); todos populam o calendário.

Uso (dry-run): python -m engine.ingestion.cbf_tabela <caminho_pdf>
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass

# nome como aparece no PDF (sem UF) -> slug do catálogo
# ordenado por comprimento desc para casar nomes longos primeiro
NOME_SLUG: dict[str, str] = {
    "Red Bull Bragantino": "bragantino",
    "Vasco da Gama": "vasco",
    "Atlético MG": "atletico-mg",
    "Athletico PR": "athletico-pr",
    "São Paulo": "sao-paulo",
    "Chapecoense": "chapecoense",
    "Internacional": "internacional",
    "Fluminense": "fluminense",
    "Corinthians": "corinthians",
    "Palmeiras": "palmeiras",
    "Botafogo": "botafogo",
    "Cruzeiro": "cruzeiro",
    "Flamengo": "flamengo",
    "Coritiba": "coritiba",
    "Mirassol": "mirassol",
    "Vitória": "vitoria",
    "Grêmio": "gremio",
    "Santos": "santos",
    "Bahia": "bahia",
    "Remo": "remo",
}
NOMES_ORD = sorted(NOME_SLUG, key=len, reverse=True)

UF = r"(?:AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)"


@dataclass
class Jogo:
    rodada: int
    data: str | None      # YYYY-MM-DD ou None
    hora: str | None      # HH:MM ou None
    casa_slug: str
    fora_slug: str
    placar_casa: int | None
    placar_fora: int | None
    estadio: str | None


def _slug_no_inicio(s: str) -> tuple[str, str] | None:
    """Casa um nome conhecido no início de s. Retorna (slug, resto)."""
    s = s.strip()
    for nome in NOMES_ORD:
        if s.startswith(nome):
            return NOME_SLUG[nome], s[len(nome):].strip()
    return None


def parse_linha(linha: str) -> Jogo | None:
    # prefixo: NNN  Rª   (num do jogo + rodada)
    m = re.match(r"^\s*(\d{3})\s+(\d{1,2})[ªa]?\s+(.*)$", linha)
    if not m:
        return None
    rodada = int(m.group(2))
    resto = m.group(3)

    # data/hora opcionais:  28/01 qua 19:00   |   "A def."   |   nada
    data = hora = None
    md = re.match(r"^(\d{2}/\d{2})\s+\w{3}\s+(\d{2}:\d{2})\s+(.*)$", resto)
    if md:
        dia_mes, hora, resto = md.group(1), md.group(2), md.group(3)
        d, mth = dia_mes.split("/")
        data = f"2026-{mth}-{d}"
    else:
        resto = re.sub(r"^A\s*def\.?\s*", "", resto)  # "A def." = data a definir

    # mandante
    a = _slug_no_inicio(resto)
    if not a:
        return None
    casa_slug, resto = a
    # remove UF do mandante
    resto = re.sub(rf"^{UF}\s*", "", resto)

    # placar opcional:  g x g   |   x
    placar_casa = placar_fora = None
    mp = re.match(r"^(\d+)\s+x\s+(\d+)\s+(.*)$", resto)
    if mp:
        placar_casa, placar_fora = int(mp.group(1)), int(mp.group(2))
        resto = mp.group(3)
    else:
        mx = re.match(r"^x\s+(.*)$", resto)
        if not mx:
            return None
        resto = mx.group(1)

    # visitante
    b = _slug_no_inicio(resto)
    if not b:
        return None
    fora_slug, resto = b
    resto = re.sub(rf"^{UF}\s*", "", resto)

    estadio = resto.strip() or None
    return Jogo(rodada, data, hora, casa_slug, fora_slug, placar_casa, placar_fora, estadio)


def parse_pdf(caminho: str) -> list[Jogo]:
    import pypdf
    r = pypdf.PdfReader(caminho)
    txt = "\n".join(p.extract_text() for p in r.pages)
    jogos = []
    for linha in txt.splitlines():
        if not linha.strip():
            continue
        j = parse_linha(linha)
        if j:
            jogos.append(j)
    return jogos


if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else "_tabela.pdf"
    jogos = parse_pdf(caminho)
    fin = [j for j in jogos if j.placar_casa is not None]
    fut = [j for j in jogos if j.placar_casa is None]
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"jogos parseados: {len(jogos)}  (finalizados {len(fin)}, futuros {len(fut)})")
    print(f"rodadas: {min(j.rodada for j in jogos)}..{max(j.rodada for j in jogos)}")
    print("exemplos finalizados:")
    for j in fin[:3]:
        print(f"  R{j.rodada} {j.data} {j.hora} {j.casa_slug} {j.placar_casa}x{j.placar_fora} {j.fora_slug}")
    print("exemplos futuros:")
    for j in fut[:3]:
        print(f"  R{j.rodada} {j.data} {j.hora} {j.casa_slug} x {j.fora_slug}")
