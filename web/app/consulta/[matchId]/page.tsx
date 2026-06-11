"use client";

import { use, useState } from "react";
import { apiPost } from "@/lib/api";

const COMPLEXIDADES = [
  { id: "simples", label: "Simples", custo: 1, desc: "1X2 · só estatístico" },
  { id: "padrao", label: "Padrão", custo: 3, desc: "Todos os mercados + LLM" },
  { id: "premium", label: "Premium", custo: 5, desc: "Completa + múltiplas + relatório" },
];

export default function ConsultaPage({ params }: { params: Promise<{ matchId: string }> }) {
  const { matchId } = use(params);
  const [resultado, setResultado] = useState<Record<string, unknown> | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [loading, setLoading] = useState<string | null>(null);

  async function consultar(complexidade: string) {
    setErro(null);
    setLoading(complexidade);
    try {
      const r = await apiPost<{ resultado: Record<string, unknown> }>("/queries", {
        match_id: Number(matchId),
        complexidade,
      });
      setResultado(r.resultado);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao consultar");
    } finally {
      setLoading(null);
    }
  }

  return (
    <div>
      <h1 className="mb-4 text-xl font-bold">Analisar partida #{matchId}</h1>

      <div className="grid gap-3 sm:grid-cols-3">
        {COMPLEXIDADES.map((c) => (
          <button
            key={c.id}
            onClick={() => consultar(c.id)}
            disabled={loading !== null}
            className="rounded border border-white/10 bg-fz-card p-4 text-left hover:border-fz-green disabled:opacity-50"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold">{c.label}</span>
              <span className="text-fz-green">{c.custo} cr</span>
            </div>
            <p className="mt-1 text-sm text-white/50">{c.desc}</p>
            {loading === c.id && <p className="mt-2 text-xs text-fz-green">analisando...</p>}
          </button>
        ))}
      </div>

      {erro && <p className="mt-4 text-sm text-red-400">{erro}</p>}

      {resultado && (
        <div className="mt-6 rounded bg-fz-card p-4">
          <h2 className="mb-2 font-semibold">Resultado</h2>
          {(resultado as { _stub?: boolean })._stub && (
            <p className="mb-2 text-xs text-yellow-400">
              ⚠ Motor em modo stub — valores zerados até as camadas serem implementadas.
            </p>
          )}
          <pre className="overflow-auto text-xs text-white/70">
            {JSON.stringify(resultado, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
