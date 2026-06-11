"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { apiGet } from "@/lib/api";

type Match = {
  id: number;
  home_team_id: number;
  away_team_id: number;
  data_hora: string;
  rodada: number | null;
  status: string;
};

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

  return (
    <div>
      <h1 className="mb-4 text-xl font-bold">Próximas partidas</h1>
      {matches.length === 0 ? (
        <p className="text-white/60">
          Nenhuma partida no catálogo ainda. (Seed da Série A pendente.)
        </p>
      ) : (
        <ul className="space-y-2">
          {matches.map((m) => (
            <li
              key={m.id}
              className="flex items-center justify-between rounded bg-fz-card px-4 py-3"
            >
              <div>
                <span className="font-medium">Time #{m.home_team_id} x Time #{m.away_team_id}</span>
                <span className="ml-2 text-sm text-white/50">
                  {new Date(m.data_hora).toLocaleString("pt-BR")}
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
      )}
    </div>
  );
}
