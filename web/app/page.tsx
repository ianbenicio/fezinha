"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { supabase } from "@/lib/supabase";
import { apiGet } from "@/lib/api";

type TeamRef = { nome: string; escudo_url: string | null };
type Match = {
  id: number; liga: string; data_hora: string | null; rodada: number | null;
  status: string; mandante: TeamRef | null; visitante: TeamRef | null;
};
type Noticia = { titulo: string; url: string; liga: string | null; publicado_em: string | null };

const fmtData = (s: string | null) =>
  s ? new Date(s).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "data a definir";

function Card({ titulo, href, children }: { titulo: string; href: string; children: React.ReactNode }) {
  return (
    <Link href={href}
      className="flex flex-col rounded-lg border border-white/10 bg-fz-card p-4 transition hover:border-fz-green">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-bold">{titulo}</h2>
        <span className="text-sm text-fz-green">ver tudo →</span>
      </div>
      <div className="flex-1 space-y-2 text-sm">{children}</div>
    </Link>
  );
}

export default function Dashboard() {
  const router = useRouter();
  const [matches, setMatches] = useState<Match[]>([]);
  const [news, setNews] = useState<Noticia[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) { router.replace("/login"); return; }
      Promise.all([
        apiGet<{ partidas: Match[] }>("/catalog/matches?status=agendado").catch(() => ({ partidas: [] })),
        apiGet<{ noticias: Noticia[] }>("/catalog/news?limit=5").catch(() => ({ noticias: [] })),
      ]).then(([m, n]) => { setMatches(m.partidas); setNews(n.noticias); })
        .finally(() => setLoading(false));
    });
  }, [router]);

  if (loading) return <p className="text-white/60">Carregando...</p>;

  const proximos = (liga: string) =>
    matches
      .filter((m) => m.liga === liga && m.data_hora)
      .sort((a, b) => (a.data_hora ?? "").localeCompare(b.data_hora ?? ""))
      .slice(0, 4);

  const cardJogos = (liga: string, label: string) => (
    <Card titulo={label} href="/calendario">
      {proximos(liga).length === 0 ? (
        <p className="text-white/40">Sem jogos agendados.</p>
      ) : (
        proximos(liga).map((m) => (
          <div key={m.id} className="border-b border-white/5 pb-1">
            <div className="font-medium">{m.mandante?.nome ?? "?"} x {m.visitante?.nome ?? "?"}</div>
            <div className="text-xs text-white/40">{fmtData(m.data_hora)}{m.rodada ? ` · R${m.rodada}` : ""}</div>
          </div>
        ))
      )}
    </Card>
  );

  return (
    <div>
      <h1 className="mb-4 text-xl font-bold">Painel</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <Card titulo="📰 Últimas notícias" href="/noticias">
          {news.length === 0 ? (
            <p className="text-white/40">Sem notícias.</p>
          ) : (
            news.slice(0, 5).map((n) => (
              <div key={n.url} className="border-b border-white/5 pb-1">
                <div className="line-clamp-2">{n.titulo}</div>
                <div className="text-xs text-white/40">{n.publicado_em ?? ""}</div>
              </div>
            ))
          )}
        </Card>
        {cardJogos("brasileirao_serie_a", "⚽ Próximos — Série A")}
        {cardJogos("brasileirao_serie_b", "⚽ Próximos — Série B")}
      </div>
    </div>
  );
}
