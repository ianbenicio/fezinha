"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { apiGet } from "@/lib/api";

type TeamRef = { nome: string };
type Match = {
  id: number;
  liga: string;
  data_hora: string | null;
  rodada: number | null;
  status: string;
  placar_casa: number | null;
  placar_fora: number | null;
  mandante: TeamRef | null;
  visitante: TeamRef | null;
};

const LIGA_NOME: Record<string, string> = {
  brasileirao_serie_a: "Série A",
  brasileirao_serie_b: "Série B",
};
const nomeLiga = (s: string) => LIGA_NOME[s] ?? s;

function startOfWeek(d: Date): Date {
  const x = new Date(d);
  const dow = (x.getDay() + 6) % 7;
  x.setDate(x.getDate() - dow);
  x.setHours(0, 0, 0, 0);
  return x;
}
function addDays(d: Date, n: number): Date {
  const x = new Date(d);
  x.setDate(x.getDate() + n);
  return x;
}
const startOfMonth = (d: Date) => new Date(d.getFullYear(), d.getMonth(), 1);
const endOfMonth = (d: Date) => new Date(d.getFullYear(), d.getMonth() + 1, 0, 23, 59, 59);
const fmtDia = (d: Date) =>
  d.toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "2-digit" });
const fmtHora = (s: string) =>
  new Date(s).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });

export default function CalendarioPage() {
  const router = useRouter();
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<"semana" | "mes">("semana");
  const [ref, setRef] = useState<Date>(new Date());
  const [liga, setLiga] = useState<string>("todas");

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        router.replace("/login");
        return;
      }
      apiGet<{ partidas: Match[] }>("/catalog/matches")
        .then((r) => {
          setMatches(r.partidas);
          // posiciona na data com jogo mais próxima de hoje
          const hoje = new Date();
          const datas = r.partidas
            .filter((m) => m.data_hora)
            .map((m) => new Date(m.data_hora as string));
          if (datas.length) {
            const maisProx = datas.reduce((a, b) =>
              Math.abs(b.getTime() - hoje.getTime()) < Math.abs(a.getTime() - hoje.getTime()) ? b : a
            );
            setRef(maisProx);
          }
        })
        .catch(() => setMatches([]))
        .finally(() => setLoading(false));
    });
  }, [router]);

  const [ini, fim] = useMemo<[Date, Date]>(() => {
    if (view === "semana") {
      const s = startOfWeek(ref);
      return [s, addDays(s, 7)];
    }
    return [startOfMonth(ref), endOfMonth(ref)];
  }, [view, ref]);

  const periodoLabel = useMemo(() => {
    if (view === "semana") {
      const s = startOfWeek(ref);
      return `${fmtDia(s)} — ${fmtDia(addDays(s, 6))}`;
    }
    return ref.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
  }, [view, ref]);

  const porRodada = useMemo(() => {
    const visiveis = matches.filter((m) => {
      if (!m.data_hora) return false;
      const d = new Date(m.data_hora);
      const okLiga = liga === "todas" || m.liga === liga;
      return d >= ini && d < fim && okLiga;
    });
    const g: Record<string, Match[]> = {};
    for (const m of visiveis) {
      const k = `${nomeLiga(m.liga)} · Rodada ${m.rodada ?? "?"}`;
      (g[k] ??= []).push(m);
    }
    for (const k in g) g[k].sort((a, b) => (a.data_hora ?? "").localeCompare(b.data_hora ?? ""));
    return g;
  }, [matches, ini, fim, liga]);

  function navega(dir: number) {
    setRef((r) =>
      view === "semana" ? addDays(r, 7 * dir) : new Date(r.getFullYear(), r.getMonth() + dir, 1)
    );
  }

  if (loading) return <p className="text-white/60">Carregando calendário...</p>;
  const rodadas = Object.entries(porRodada);

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold">Calendário</h1>
        <div className="flex rounded-lg border border-white/10 p-0.5 text-sm">
          {(["semana", "mes"] as const).map((v) => (
            <button key={v} onClick={() => setView(v)}
              className={`rounded-md px-3 py-1 ${view === v ? "bg-fz-green text-black" : "text-white/60"}`}>
              {v === "semana" ? "Semanal" : "Mensal"}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <button onClick={() => navega(-1)} className="rounded bg-fz-card px-3 py-1 hover:text-fz-green">‹</button>
          <span className="min-w-[180px] text-center font-medium capitalize">{periodoLabel}</span>
          <button onClick={() => navega(1)} className="rounded bg-fz-card px-3 py-1 hover:text-fz-green">›</button>
        </div>
        <select value={liga} onChange={(e) => setLiga(e.target.value)}
          className="rounded bg-fz-card px-3 py-1 text-sm outline-none">
          <option value="todas">Todos os campeonatos</option>
          <option value="brasileirao_serie_a">Série A</option>
          <option value="brasileirao_serie_b">Série B</option>
        </select>
      </div>

      {rodadas.length === 0 ? (
        <p className="text-white/50">Nenhum jogo neste período. Use ‹ › para navegar.</p>
      ) : (
        <div className="space-y-6">
          {rodadas.map(([titulo, jogos]) => (
            <section key={titulo}>
              <h2 className="mb-2 flex items-center gap-2 font-bold">
                <span className="rounded bg-fz-green/20 px-2 py-0.5 text-sm text-fz-green">{jogos.length}</span>
                {titulo}
              </h2>
              <ul className="space-y-2">
                {jogos.map((m) => {
                  const fim = m.status === "encerrado";
                  return (
                    <li key={m.id} className="flex items-center justify-between rounded bg-fz-card px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-24 text-sm text-white/50">
                          <div>{m.data_hora ? fmtDia(new Date(m.data_hora)) : "—"}</div>
                          <div className="text-fz-green">{m.data_hora ? fmtHora(m.data_hora) : ""}</div>
                        </div>
                        <span className="font-medium">
                          {m.mandante?.nome ?? "?"}
                          {fim ? (
                            <span className="mx-2 rounded bg-black/40 px-2 py-0.5 text-fz-green">
                              {m.placar_casa} - {m.placar_fora}
                            </span>
                          ) : (
                            <span className="mx-2 text-white/40">x</span>
                          )}
                          {m.visitante?.nome ?? "?"}
                        </span>
                      </div>
                      <button onClick={() => router.push(`/consulta/${m.id}`)}
                        className="rounded bg-fz-green px-3 py-1 text-sm font-semibold text-black">
                        {fim ? "Rever" : "Analisar"}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
