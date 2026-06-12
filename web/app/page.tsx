"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { supabase } from "@/lib/supabase";
import { apiGet } from "@/lib/api";

type TeamRef = { id: number; nome: string; slug: string; escudo_url: string | null };

type Match = {
  id: number;
  liga: string;
  home_team_id: number;
  away_team_id: number;
  data_hora: string | null;
  rodada: number | null;
  status: string;
  placar_casa: number | null;
  placar_fora: number | null;
  mandante: TeamRef | null;
  visitante: TeamRef | null;
};

const LIGA_NOME: Record<string, string> = {
  brasileirao_serie_a: "Brasileirão Série A",
  brasileirao_serie_b: "Brasileirão Série B",
};
const nomeLiga = (s: string) =>
  LIGA_NOME[s] ?? s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

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
      apiGet<{ partidas: Match[] }>("/catalog/matches")
        .then((r) => setMatches(r.partidas))
        .catch(() => setMatches([]))
        .finally(() => setLoading(false));
    });
  }, [router]);

  if (loading) return <p className="text-white/60">Carregando partidas...</p>;
  if (matches.length === 0)
    return <p className="text-white/60">Nenhuma partida no catálogo ainda.</p>;

  // agrupa por liga; dentro, mais recentes primeiro; limita
  const grupos: Record<string, Match[]> = {};
  for (const m of matches) (grupos[m.liga] ??= []).push(m);
  for (const k in grupos)
    grupos[k].sort((a, b) => (b.data_hora ?? "").localeCompare(a.data_hora ?? ""));

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Partidas</h1>
        <Link href="/calendario" className="text-sm text-fz-green hover:underline">
          Ver calendário completo →
        </Link>
      </div>

      {Object.entries(grupos).map(([liga, jogos]) => (
        <section key={liga}>
          <h2 className="mb-3 flex items-center gap-2 text-lg font-bold">
            <span className="rounded bg-fz-green/20 px-2 py-0.5 text-sm text-fz-green">
              {jogos.length}
            </span>
            {nomeLiga(liga)}
          </h2>
          <ul className="space-y-2">
            {jogos.slice(0, 12).map((m) => {
              const fim = m.status === "encerrado";
              return (
                <li key={m.id} className="flex items-center justify-between rounded bg-fz-card px-4 py-3">
                  <div>
                    <span className="font-medium">
                      {m.mandante?.nome ?? `Time #${m.home_team_id}`}
                      {fim ? (
                        <span className="mx-2 rounded bg-black/40 px-2 py-0.5 text-fz-green">
                          {m.placar_casa} - {m.placar_fora}
                        </span>
                      ) : (
                        <span className="mx-2 text-white/40">x</span>
                      )}
                      {m.visitante?.nome ?? `Time #${m.away_team_id}`}
                    </span>
                    <span className="ml-2 text-sm text-white/50">
                      {m.rodada ? `Rodada ${m.rodada}` : ""}
                      {m.data_hora
                        ? ` · ${new Date(m.data_hora).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" })}`
                        : " · data a definir"}
                    </span>
                  </div>
                  <button
                    onClick={() => router.push(`/consulta/${m.id}`)}
                    className="rounded bg-fz-green px-3 py-1 text-sm font-semibold text-black"
                  >
                    {fim ? "Rever" : "Analisar"}
                  </button>
                </li>
              );
            })}
          </ul>
        </section>
      ))}
    </div>
  );
}
