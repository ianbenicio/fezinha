// Dashboard/painel — componente presentacional (props-driven, sem fetch).
// Usado por app/page.tsx (dados reais) e por app/preview (mock), para
// permitir iterar o visual sem backend.

import Link from "next/link";
import type { ReactNode } from "react";
import type { Match, Noticia } from "@/lib/types";
import { Loading } from "@/components/states";

const LIGA_LABEL: Record<string, string> = {
  brasileirao_serie_a: "Série A",
  brasileirao_serie_b: "Série B",
};

const fmtData = (s: string | null) =>
  s
    ? new Date(s).toLocaleString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "data a definir";

function Card({
  titulo,
  href,
  cta = "ver tudo",
  children,
}: {
  titulo: string;
  href: string;
  cta?: string;
  children: ReactNode;
}) {
  return (
    <Link
      href={href}
      className="group flex flex-col rounded-lg border border-white/10 bg-fz-card p-4 transition hover:border-fz-green"
    >
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-bold">{titulo}</h2>
        <span className="text-sm text-fz-green opacity-0 transition group-hover:opacity-100">
          {cta} →
        </span>
      </div>
      <div className="flex-1 space-y-2 text-sm">{children}</div>
    </Link>
  );
}

function Escudo({ url, nome }: { url?: string | null; nome: string }) {
  if (!url) {
    return (
      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-white/10 text-[9px] text-white/60">
        {nome.slice(0, 2).toUpperCase()}
      </span>
    );
  }
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={url} alt="" className="h-5 w-5 shrink-0 object-contain" />;
}

function MatchRow({ m }: { m: Match }) {
  return (
    <div className="flex items-center justify-between gap-2 border-b border-white/5 pb-1.5 last:border-0">
      <div className="flex min-w-0 items-center gap-1.5">
        <Escudo url={m.mandante?.escudo_url} nome={m.mandante?.nome ?? "?"} />
        <span className="truncate font-medium">{m.mandante?.nome ?? "?"}</span>
        <span className="text-white/30">×</span>
        <span className="truncate font-medium">{m.visitante?.nome ?? "?"}</span>
        <Escudo url={m.visitante?.escudo_url} nome={m.visitante?.nome ?? "?"} />
      </div>
      <div className="shrink-0 text-right text-xs text-white/40">
        {fmtData(m.data_hora)}
        {m.rodada ? ` · R${m.rodada}` : ""}
      </div>
    </div>
  );
}

export function DashboardView({
  matches,
  news,
  loading,
}: {
  matches: Match[];
  news: Noticia[];
  loading?: boolean;
}) {
  if (loading) return <Loading label="Carregando painel..." />;

  const proximos = (liga: string) =>
    matches
      .filter((m) => m.liga === liga && m.data_hora)
      .sort((a, b) => (a.data_hora ?? "").localeCompare(b.data_hora ?? ""))
      .slice(0, 4);

  const cardJogos = (liga: string) => {
    const lista = proximos(liga);
    return (
      <Card titulo={`⚽ Próximos — ${LIGA_LABEL[liga] ?? liga}`} href="/calendario">
        {lista.length === 0 ? (
          <p className="text-white/40">Sem jogos agendados.</p>
        ) : (
          lista.map((m) => <MatchRow key={m.id} m={m} />)
        )}
      </Card>
    );
  };

  return (
    <div>
      <header className="mb-5">
        <h1 className="text-2xl font-bold">Painel</h1>
        <p className="text-sm text-white/40">Próximos jogos e notícias do Brasileirão.</p>
      </header>
      <div className="grid gap-4 md:grid-cols-3">
        <Card titulo="📰 Últimas notícias" href="/noticias" cta="todas">
          {news.length === 0 ? (
            <p className="text-white/40">Sem notícias.</p>
          ) : (
            news.slice(0, 5).map((n) => (
              <div key={n.url} className="border-b border-white/5 pb-1.5 last:border-0">
                <div className="line-clamp-2">{n.titulo}</div>
                <div className="text-xs text-white/40">{n.publicado_em ?? ""}</div>
              </div>
            ))
          )}
        </Card>
        {cardJogos("brasileirao_serie_a")}
        {cardJogos("brasileirao_serie_b")}
      </div>
    </div>
  );
}
