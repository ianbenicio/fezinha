"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { supabase } from "@/lib/supabase";
import { apiGet } from "@/lib/api";
import type { TeamSummary } from "@/lib/types";
import { mockTeams } from "@/lib/mock";
import { Loading, Banner } from "@/components/states";

const LIGA_LABEL: Record<string, string> = {
  brasileirao_serie_a: "Série A",
  brasileirao_serie_b: "Série B",
};

function TeamCard({ t }: { t: TeamSummary }) {
  return (
    <Link
      href={`/times/${t.id}`}
      className="flex items-center gap-3 rounded-lg border border-white/10 bg-fz-card p-3 transition hover:border-fz-green"
    >
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/10 text-xs text-white/60">
        {t.nome.slice(0, 2).toUpperCase()}
      </span>
      <div className="min-w-0">
        <div className="truncate font-medium">{t.nome}</div>
        <div className="text-xs text-white/40">
          {LIGA_LABEL[t.liga] ?? t.liga}
          {t.posicao != null ? ` · ${t.posicao}º · ${t.pontos} pts` : ""}
        </div>
      </div>
    </Link>
  );
}

export default function TimesPage() {
  const router = useRouter();
  const [teams, setTeams] = useState<TeamSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [mockUsado, setMockUsado] = useState(false);
  const [filtro, setFiltro] = useState("todas");

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        router.replace("/login");
        return;
      }
      apiGet<{ times: TeamSummary[] }>("/catalog/teams")
        .then((r) => {
          if (!Array.isArray(r?.times)) throw new Error("shape inesperado de /catalog/teams");
          setTeams(r.times);
        })
        .catch(() => {
          setTeams(mockTeams);
          setMockUsado(true);
        })
        .finally(() => setLoading(false));
    });
  }, [router]);

  if (loading) return <Loading label="Carregando times..." />;

  const visiveis = filtro === "todas" ? teams : teams.filter((t) => t.liga === filtro);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">Times</h1>
        <select
          value={filtro}
          onChange={(e) => setFiltro(e.target.value)}
          className="rounded bg-fz-card px-3 py-1 text-sm outline-none"
        >
          <option value="todas">Todos</option>
          <option value="brasileirao_serie_a">Série A</option>
          <option value="brasileirao_serie_b">Série B</option>
        </select>
      </div>

      {mockUsado && (
        <Banner tone="warn" titulo="Dados de exemplo">
          Endpoint <code>/catalog/teams</code> pendente (Codex). Mostrando mock.
        </Banner>
      )}

      <div className="mt-4 grid gap-3 sm:grid-cols-2 md:grid-cols-3">
        {visiveis.map((t) => (
          <TeamCard key={t.id} t={t} />
        ))}
      </div>
    </div>
  );
}
