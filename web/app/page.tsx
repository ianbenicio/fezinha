"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { apiGet } from "@/lib/api";

type TeamRef = { id: number; nome: string; slug: string; escudo_url: string | null };

type Match = {
  id: number;
  liga: string;
  home_team_id: number;
  away_team_id: number;
  data_hora: string;
  rodada: number | null;
  status: string;
  mandante: TeamRef | null;
  visitante: TeamRef | null;
};

const LIGA_NOME: Record<string, string> = {
  brasileirao_serie_a: "Brasileirão Série A",
  brasileirao_serie_b: "Brasileirão Série B",
};

function nomeLiga(slug: string): string {
  return (
    LIGA_NOME[slug] ??
    slug.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
  );
}

export default function Dashboard() {
  const router = useRouter();
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        router.replace("/login");
        return;
      }
      apiGet<{ partidas: Match[] }>("/catalog/matches?status=agendado")
        .then((r) => setMatches(r.partidas))
        .catch(() => setMatches([]))
        .finally(() => setLoading(false));
    });
  }, [router]);

  if (loading) return <p className="text-white/60">Carregando partidas...</p>;

  if (matches.length === 0) {
    return (
      <p className="text-white/60">
        Nenhuma partida no catálogo ainda. (Seed/ingestão pendente.)
      </p>
    );
  }

  // agrupa por campeonato
  const grupos: Record<string, Match[]> = {};
  for (const m of matches) (grupos[m.liga] ??= []).push(m);

  return (
    <div className="space-y-8">
      {Object.entries(grupos).map(([liga, jogos]) => (
        <section key={liga}>
          <h2 className="mb-3 flex items-center gap-2 text-lg font-bold">
            <span className="rounded bg-fz-green/20 px-2 py-0.5 text-sm text-fz-green">
              {jogos.length}
            </span>
            {nomeLiga(liga)}
          </h2>
          <ul className="space-y-2">
            {jogos.map((m) => (
              <li
                key={m.id}
                className="flex items-center justify-between rounded bg-fz-card px-4 py-3"
              >
                <div>
                  <span className="font-medium">
                    {m.mandante?.nome ?? `Time #${m.home_team_id}`} x{" "}
                    {m.visitante?.nome ?? `Time #${m.away_team_id}`}
                  </span>
                  <span className="ml-2 text-sm text-white/50">
                    {new Date(m.data_hora).toLocaleString("pt-BR", {
                      dateStyle: "short",
                      timeStyle: "short",
                    })}
                    {m.rodada ? ` · Rodada ${m.rodada}` : ""}
                  </span>
                </div>
                <button
                  onClick={() => router.push(`/consulta/${m.id}`)}
                  className="rounded bg-fz-green px-3 py-1 text-sm font-semibold text-black"
                >
                  Analisar
                </button>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
