// Detalhe do time — presentacional (props-driven). 6 blocos:
// identidade · radar · estatisticas · elenco (placeholder) · jogos · noticias.
// Ver docs/ux/team-section.md. Mock-first; sem fetch aqui.

import type { CSSProperties } from "react";
import type { Match, ResultadoForma, TeamDetail } from "@/lib/types";
import { Banner, EmptyState } from "@/components/states";
import { TeamRadar } from "@/components/TeamRadar";

const LIGA_LABEL: Record<string, string> = {
  brasileirao_serie_a: "Série A",
  brasileirao_serie_b: "Série B",
};

const FORMA_CLS: Record<ResultadoForma, string> = {
  V: "bg-fz-green/20 text-fz-green",
  E: "bg-white/10 text-white/50",
  D: "bg-red-500/20 text-red-300",
};

const fmtData = (s: string | null) =>
  s ? new Date(s).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "—";

function Escudo({ url, nome, px = 32 }: { url: string | null; nome: string; px?: number }) {
  const style: CSSProperties = { width: px, height: px };
  if (!url) {
    return (
      <span
        style={style}
        className="flex shrink-0 items-center justify-center rounded-full bg-white/10 text-xs text-white/60"
      >
        {nome.slice(0, 2).toUpperCase()}
      </span>
    );
  }
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={url} alt="" style={style} className="shrink-0 object-contain" />;
}

function MatchRow({ m }: { m: Match }) {
  const fim = m.status === "encerrado";
  return (
    <li className="flex items-center justify-between rounded bg-black/20 px-3 py-2 text-sm">
      <span className="truncate">
        {m.mandante?.nome ?? "?"}
        {fim ? (
          <span className="mx-2 text-fz-green">
            {m.placar_casa}-{m.placar_fora}
          </span>
        ) : (
          <span className="mx-2 text-white/30">×</span>
        )}
        {m.visitante?.nome ?? "?"}
      </span>
      <span className="shrink-0 text-xs text-white/40">{fmtData(m.data_hora)}</span>
    </li>
  );
}

function Section({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg bg-fz-card p-4">
      <h2 className="mb-3 font-semibold">{titulo}</h2>
      {children}
    </section>
  );
}

export function TeamView({ detail }: { detail: TeamDetail }) {
  const t = detail.resumo;
  return (
    <div className="space-y-5">
      {/* 1. Identidade */}
      <header className="flex flex-wrap items-center gap-4 rounded-lg bg-fz-card p-5">
        <Escudo url={t.escudo_url} nome={t.nome} px={48} />
        <div className="min-w-0">
          <h1 className="text-2xl font-bold">{t.nome}</h1>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-white/50">
            <span>{LIGA_LABEL[t.liga] ?? t.liga}</span>
            {t.posicao != null && (
              <span>
                {t.posicao}º · {t.pontos} pts
              </span>
            )}
            {t.forma && t.forma.length > 0 && (
              <span className="flex gap-1">
                {t.forma.map((f, i) => (
                  <span key={i} className={`rounded px-1.5 py-0.5 text-xs ${FORMA_CLS[f]}`}>
                    {f}
                  </span>
                ))}
              </span>
            )}
          </div>
        </div>
      </header>

      {/* 2. Radar */}
      {detail.radar ? (
        <TeamRadar radar={detail.radar} />
      ) : (
        <EmptyState titulo="Radar indisponível" dica="Aguardando dados do motor." />
      )}

      {/* 3. Estatísticas */}
      <Section titulo="Estatísticas">
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {detail.estatisticas.map((s) => (
            <div key={s.label} className="rounded bg-black/20 px-3 py-2">
              <div className="text-xs text-white/50">{s.label}</div>
              <div className="text-lg font-semibold text-fz-green">{s.valor}</div>
            </div>
          ))}
        </div>
      </Section>

      {/* 4. Elenco */}
      <Section titulo="Elenco">
        {!detail.elenco_disponivel || detail.elenco.length === 0 ? (
          <Banner tone="muted" titulo="Elenco indisponível">
            Dados de jogadores/lesões ainda não ingeridos — requer fonte paga (API-Football PRO). Sem inventar jogador.
          </Banner>
        ) : (
          <ul className="divide-y divide-white/5 text-sm">
            {detail.elenco.map((j) => (
              <li key={j.nome} className="flex items-center justify-between py-1.5">
                <span>
                  {j.nome} <span className="text-white/40">· {j.posicao}</span>
                </span>
                <span className="text-xs text-white/40">{j.status ?? ""}</span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      {/* 5. Jogos */}
      <Section titulo="Jogos">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <div className="mb-2 text-xs text-white/40">Próximos</div>
            {detail.proximos.length === 0 ? (
              <p className="text-sm text-white/40">Sem jogos agendados.</p>
            ) : (
              <ul className="space-y-2">
                {detail.proximos.map((m) => (
                  <MatchRow key={m.id} m={m} />
                ))}
              </ul>
            )}
          </div>
          <div>
            <div className="mb-2 text-xs text-white/40">Últimos</div>
            {detail.ultimos.length === 0 ? (
              <p className="text-sm text-white/40">Sem resultados recentes.</p>
            ) : (
              <ul className="space-y-2">
                {detail.ultimos.map((m) => (
                  <MatchRow key={m.id} m={m} />
                ))}
              </ul>
            )}
          </div>
        </div>
      </Section>

      {/* 6. Notícias */}
      <Section titulo="Notícias">
        {detail.noticias_filtro_aproximado && (
          <p className="mb-2 text-xs text-white/30">Filtro aproximado por nome (sem tag de time ainda).</p>
        )}
        {detail.noticias.length === 0 ? (
          <p className="text-sm text-white/40">Sem notícias.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {detail.noticias.map((n) => (
              <li key={n.url}>
                <a href={n.url} target="_blank" rel="noopener noreferrer" className="text-white/80 hover:text-fz-green">
                  {n.titulo}
                </a>
              </li>
            ))}
          </ul>
        )}
      </Section>
    </div>
  );
}
