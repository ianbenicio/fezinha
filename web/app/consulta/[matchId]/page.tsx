"use client";

import { use, useState } from "react";
import { apiPost } from "@/lib/api";

const COMPLEXIDADES = [
  { id: "simples", label: "Simples", custo: 1, desc: "1X2 · só estatístico" },
  { id: "padrao", label: "Padrão", custo: 3, desc: "Todos os mercados + LLM" },
  { id: "premium", label: "Premium", custo: 5, desc: "Completa + múltiplas + relatório" },
];

type TraceItem = {
  camada: string;
  topico: string;
  status: string;
  entrada: unknown;
  saida: unknown;
};

type Resultado = {
  partida?: { mandante: string; visitante: string };
  baseline?: boolean;
  agregador?: {
    resultado: {
      prob_casa: number; prob_empate: number; prob_visitante: number;
      resultado_mais_provavel: string; placar_provavel: string;
    };
    gols: { over_15: number; over_25: number; over_35: number; btts: number };
    escanteios: { over_85: number; over_95: number; over_105: number };
  };
  trace?: TraceItem[];
};

function pct(n: number) {
  return `${(n * 100).toFixed(1)}%`;
}

function Barra({ label, valor, cor }: { label: string; valor: number; cor: string }) {
  return (
    <div className="mb-2">
      <div className="mb-1 flex justify-between text-sm">
        <span>{label}</span>
        <span className="font-semibold">{pct(valor)}</span>
      </div>
      <div className="h-3 w-full overflow-hidden rounded bg-black/30">
        <div className="h-full rounded" style={{ width: pct(valor), background: cor }} />
      </div>
    </div>
  );
}

function Mercado({ label, valor }: { label: string; valor: number }) {
  return (
    <div className="rounded bg-black/20 px-3 py-2">
      <div className="text-xs text-white/50">{label}</div>
      <div className="text-lg font-semibold text-fz-green">{pct(valor)}</div>
    </div>
  );
}

const STATUS_COR: Record<string, string> = {
  ok: "text-fz-green",
  baseline: "text-yellow-400",
  pendente: "text-white/30",
};

export default function ConsultaPage({ params }: { params: Promise<{ matchId: string }> }) {
  const { matchId } = use(params);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [logAberto, setLogAberto] = useState(false);

  async function consultar(complexidade: string) {
    setErro(null);
    setLoading(complexidade);
    try {
      const r = await apiPost<{ resultado: Resultado }>("/queries", {
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

  const ag = resultado?.agregador;

  return (
    <div>
      <h1 className="mb-1 text-xl font-bold">
        {resultado?.partida
          ? `${resultado.partida.mandante} x ${resultado.partida.visitante}`
          : `Analisar partida #${matchId}`}
      </h1>
      <p className="mb-4 text-sm text-white/40">Escolha a profundidade da análise</p>

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

      {ag && (
        <div className="mt-6 space-y-5">
          {/* Resultado 1X2 */}
          <section className="rounded-lg bg-fz-card p-5">
            <div className="mb-3 flex items-baseline justify-between">
              <h2 className="font-semibold">Resultado provável</h2>
              <span className="text-sm text-white/50">
                placar mais provável: <b className="text-white/80">{ag.resultado.placar_provavel}</b>
              </span>
            </div>
            <Barra label={resultado?.partida?.mandante ?? "Casa"} valor={ag.resultado.prob_casa} cor="#16a34a" />
            <Barra label="Empate" valor={ag.resultado.prob_empate} cor="#6b7280" />
            <Barra label={resultado?.partida?.visitante ?? "Visitante"} valor={ag.resultado.prob_visitante} cor="#3b82f6" />
          </section>

          {/* Mercados de gols */}
          <section className="rounded-lg bg-fz-card p-5">
            <h2 className="mb-3 font-semibold">Gols</h2>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <Mercado label="Mais de 1.5" valor={ag.gols.over_15} />
              <Mercado label="Mais de 2.5" valor={ag.gols.over_25} />
              <Mercado label="Mais de 3.5" valor={ag.gols.over_35} />
              <Mercado label="Ambos marcam" valor={ag.gols.btts} />
            </div>
          </section>

          {/* Escanteios */}
          <section className="rounded-lg bg-fz-card p-5">
            <h2 className="mb-3 font-semibold">Escanteios</h2>
            <div className="grid grid-cols-3 gap-2">
              <Mercado label="Mais de 8.5" valor={ag.escanteios.over_85} />
              <Mercado label="Mais de 9.5" valor={ag.escanteios.over_95} />
              <Mercado label="Mais de 10.5" valor={ag.escanteios.over_105} />
            </div>
          </section>

          {resultado?.baseline && (
            <p className="rounded bg-yellow-500/10 px-3 py-2 text-xs text-yellow-400">
              ⚠ Análise em modo baseline — os times ainda não têm força individual no
              sistema (ingestão pendente). Por isso jogos diferentes dão números parecidos.
            </p>
          )}

          {/* Log de processo */}
          {resultado?.trace && (
            <section className="rounded-lg border border-white/10">
              <button
                onClick={() => setLogAberto(!logAberto)}
                className="flex w-full items-center justify-between px-5 py-3 text-left"
              >
                <span className="font-semibold">🔎 Log do processo ({resultado.trace.length} camadas)</span>
                <span className="text-white/40">{logAberto ? "▲" : "▼"}</span>
              </button>
              {logAberto && (
                <div className="space-y-2 px-3 pb-3">
                  {resultado.trace.map((t, i) => (
                    <details key={i} className="rounded bg-black/20 px-3 py-2 text-sm">
                      <summary className="cursor-pointer">
                        <span className={STATUS_COR[t.status] ?? "text-white"}>●</span>{" "}
                        <b>{t.camada}</b> — {t.topico}{" "}
                        <span className="text-xs text-white/40">[{t.status}]</span>
                      </summary>
                      <div className="mt-2 grid gap-2 sm:grid-cols-2">
                        <div>
                          <div className="text-xs text-white/40">entrada</div>
                          <pre className="overflow-auto rounded bg-black/30 p-2 text-xs text-white/70">
                            {JSON.stringify(t.entrada, null, 2)}
                          </pre>
                        </div>
                        <div>
                          <div className="text-xs text-white/40">saída</div>
                          <pre className="overflow-auto rounded bg-black/30 p-2 text-xs text-white/70">
                            {JSON.stringify(t.saida, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </details>
                  ))}
                </div>
              )}
            </section>
          )}
        </div>
      )}
    </div>
  );
}
