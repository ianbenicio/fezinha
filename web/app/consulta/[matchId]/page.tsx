"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { apiGet, apiPost } from "@/lib/api";
import type { Partida, Resultado } from "@/lib/types";
import { Banner, EngineModeBanner, NoBanca } from "@/components/states";

const COMPLEXIDADES = [
  { id: "simples", label: "Simples", custo: 1, desc: "1X2 · só estatístico" },
  { id: "padrao", label: "Padrão", custo: 3, desc: "Todos os mercados + LLM" },
  { id: "premium", label: "Premium", custo: 5, desc: "Completa + múltiplas + relatório" },
];

const LEITURA_COMP: Record<string, string> = {
  vantagem_forte_casa: "Vantagem forte do mandante",
  vantagem_casa: "Vantagem do mandante",
  equilibrio: "Equilíbrio",
  vantagem_fora: "Vantagem do visitante",
  vantagem_forte_fora: "Vantagem forte do visitante",
};

const pct = (n: number) => `${(n * 100).toFixed(1)}%`;

function Barra({ label, valor, cor }: { label: string; valor: number; cor: string }) {
  return (
    <div className="mb-2">
      <div className="mb-1 flex justify-between text-sm">
        <span>{label}</span><span className="font-semibold">{pct(valor)}</span>
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
  ok: "text-fz-green", baseline: "text-yellow-400", pendente: "text-white/30",
};

export default function ConsultaPage({ params }: { params: Promise<{ matchId: string }> }) {
  const { matchId } = use(params);
  const router = useRouter();
  const [partida, setPartida] = useState<Partida | null>(null);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [logAberto, setLogAberto] = useState(false);
  const [metaErro, setMetaErro] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        router.replace("/login");
        return;
      }
      apiGet<{ partida: Partida }>(`/catalog/matches/${matchId}`)
        .then((r) => {
          if (!r?.partida) throw new Error("shape inesperado de /catalog/matches/{id}");
          setPartida(r.partida);
        })
        .catch(() => {
          setPartida(null);
          setMetaErro(true);
        });
    });
  }, [matchId, router]);

  async function consultar(complexidade: string) {
    setErro(null);
    setLoading(complexidade);
    try {
      const r = await apiPost<{ resultado: Resultado }>("/queries", {
        match_id: Number(matchId), complexidade,
      });
      setResultado(r.resultado);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao consultar");
    } finally {
      setLoading(null);
    }
  }

  const ag = resultado?.agregador;
  const titulo = partida?.mandante && partida?.visitante
    ? `${partida.mandante.nome} x ${partida.visitante.nome}`
    : `Partida #${matchId}`;

  return (
    <div>
      {/* Header da partida */}
      <div className="mb-5 rounded-lg bg-fz-card p-5">
        <h1 className="text-2xl font-bold">{titulo}</h1>
        {partida && (
          <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-sm text-white/60">
            <span>📅 {new Date(partida.data_hora).toLocaleString("pt-BR", {
              dateStyle: "short", timeStyle: "short",
            })}</span>
            {partida.local && <span>📍 {partida.local}</span>}
            {partida.rodada && <span>🏆 Rodada {partida.rodada}</span>}
            <span className="capitalize">● {partida.status}</span>
          </div>
        )}
      </div>

      {metaErro && (
        <Banner tone="muted" titulo="Metadados indisponíveis">
          Não foi possível carregar os dados da partida. A análise abaixo ainda funciona.
        </Banner>
      )}

      <p className="mb-3 text-sm text-white/40">Escolha a profundidade da análise</p>
      <div className="grid gap-3 sm:grid-cols-3">
        {COMPLEXIDADES.map((c) => (
          <button key={c.id} onClick={() => consultar(c.id)} disabled={loading !== null}
            className="rounded border border-white/10 bg-fz-card p-4 text-left hover:border-fz-green disabled:opacity-50">
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
          {/* Estado do motor + confiança + alertas (contract-v0) */}
          <EngineModeBanner modo={ag.modo} />
          {resultado?.alertas?.map((a, i) => (
            <Banner
              key={i}
              tone={a.severidade === "bloqueio" ? "error" : a.severidade === "aviso" ? "warn" : "info"}
              titulo={a.tipo}
            >
              {a.descricao}
            </Banner>
          ))}
          {resultado?.indice_confianca && (
            <p className="text-xs text-white/50">
              Confiança:{" "}
              {resultado.indice_confianca.valor == null
                ? "indisponível"
                : pct(resultado.indice_confianca.valor)}{" "}
              · {resultado.indice_confianca.leitura}
            </p>
          )}

          {/* Força Comparativa (IFC) */}
          {resultado?.forca_comparativa && (() => {
            const fc = resultado.forca_comparativa!;
            const cm = partida?.mandante?.nome ?? "Mandante";
            const cv = partida?.visitante?.nome ?? "Visitante";
            return (
              <section className="rounded-lg bg-fz-card p-5">
                <div className="mb-1 flex items-baseline justify-between">
                  <h2 className="font-semibold">Força comparativa</h2>
                  <span className="text-sm text-fz-green">{LEITURA_COMP[fc.leitura] ?? fc.leitura}</span>
                </div>
                <p className="mb-3 text-xs text-white/40">
                  Leitura alternativa — não é a previsão principal.
                </p>
                <div className="mb-1 flex justify-between text-sm">
                  <span>{cm}</span><span className="font-bold">{fc.mandante.ifc}<span className="text-white/40">/100</span></span>
                </div>
                <div className="mb-3 h-3 w-full overflow-hidden rounded bg-black/30">
                  <div className="h-full rounded bg-fz-green" style={{ width: `${fc.mandante.ifc}%` }} />
                </div>
                <div className="mb-1 flex justify-between text-sm">
                  <span>{cv}</span><span className="font-bold">{fc.visitante.ifc}<span className="text-white/40">/100</span></span>
                </div>
                <div className="mb-3 h-3 w-full overflow-hidden rounded bg-black/30">
                  <div className="h-full rounded" style={{ width: `${fc.visitante.ifc}%`, background: "#3b82f6" }} />
                </div>
                <p className="text-xs text-white/50">
                  50 = média da liga · diferença {fc.diferenca_ifc > 0 ? "+" : ""}{fc.diferenca_ifc} →
                  expectativa do mandante <b className="text-white/80">{pct(fc.expectativa_mandante)}</b>
                  {" "}(de {fc.jogos_no_grafo} jogos)
                </p>
                {fc.adversarios_comuns.length > 0 && (
                  <div className="mt-3 border-t border-white/10 pt-3">
                    <div className="mb-2 text-xs text-white/40">Adversários em comum</div>
                    <ul className="space-y-1 text-sm">
                      {fc.adversarios_comuns.map((a, i) => (
                        <li key={i} className="flex flex-wrap gap-x-2">
                          <span className="text-white/60">vs {a.adversario}:</span>
                          <span>{cm} {a.resultado_mandante}</span>
                          <span className="text-white/40">·</span>
                          <span>{cv} {a.resultado_visitante}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </section>
            );
          })()}

          <section className="rounded-lg bg-fz-card p-5">
            <div className="mb-3 flex items-baseline justify-between">
              <h2 className="font-semibold">Resultado provável</h2>
              <span className="text-sm text-white/50">
                placar provável: <b className="text-white/80">{ag.resultado.placar_provavel}</b>
              </span>
            </div>
            <Barra label={partida?.mandante?.nome ?? "Casa"} valor={ag.resultado.prob_casa} cor="#16a34a" />
            <Barra label="Empate" valor={ag.resultado.prob_empate} cor="#6b7280" />
            <Barra label={partida?.visitante?.nome ?? "Visitante"} valor={ag.resultado.prob_visitante} cor="#3b82f6" />
          </section>

          <section className="rounded-lg bg-fz-card p-5">
            <h2 className="mb-3 font-semibold">Gols</h2>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <Mercado label="Mais de 1.5" valor={ag.gols.over_15} />
              <Mercado label="Mais de 2.5" valor={ag.gols.over_25} />
              <Mercado label="Mais de 3.5" valor={ag.gols.over_35} />
              <Mercado label="Ambos marcam" valor={ag.gols.btts} />
            </div>
          </section>

          <section className="rounded-lg bg-fz-card p-5">
            <h2 className="mb-3 font-semibold">Escanteios</h2>
            <div className="grid grid-cols-3 gap-2">
              <Mercado label="Mais de 8.5" valor={ag.escanteios.over_85} />
              <Mercado label="Mais de 9.5" valor={ag.escanteios.over_95} />
              <Mercado label="Mais de 10.5" valor={ag.escanteios.over_105} />
            </div>
          </section>

          {resultado?.banca && resultado.banca.recomendacoes.length === 0 && (
            <NoBanca nota={resultado.banca.nota} />
          )}

          {/* Log / descrição das camadas */}
          {resultado?.trace && (
            <section className="rounded-lg border border-white/10">
              <button onClick={() => setLogAberto(!logAberto)}
                className="flex w-full items-center justify-between px-5 py-3 text-left">
                <span className="font-semibold">📋 Como esta análise foi feita ({resultado.trace.length} camadas)</span>
                <span className="text-white/40">{logAberto ? "▲" : "▼"}</span>
              </button>
              {logAberto && (
                <div className="space-y-2 px-3 pb-3">
                  {resultado.trace.map((t, i) => (
                    <details key={i} className="rounded bg-black/20 px-3 py-2 text-sm">
                      <summary className="cursor-pointer list-none">
                        <span className={STATUS_COR[t.status] ?? "text-white"}>●</span>{" "}
                        <b>{t.topico}</b>{" "}
                        <span className="text-xs text-white/40">[{t.status}]</span>
                        {t.resumo && <div className="ml-4 mt-1 text-white/80">{t.resumo}</div>}
                      </summary>
                      <div className="ml-4 mt-2 space-y-2">
                        {t.justificativa && (
                          <p className="text-white/60"><b className="text-white/40">Por quê: </b>{t.justificativa}</p>
                        )}
                        {t.fonte && (
                          <p className="text-white/60"><b className="text-white/40">Fonte: </b>{t.fonte}</p>
                        )}
                        {(t.entrada != null || t.saida != null) && (
                          <div className="grid gap-2 sm:grid-cols-2">
                            <div>
                              <div className="text-xs text-white/40">entrada</div>
                              <pre className="overflow-auto rounded bg-black/30 p-2 text-xs text-white/60">
                                {JSON.stringify(t.entrada, null, 2)}
                              </pre>
                            </div>
                            <div>
                              <div className="text-xs text-white/40">saída</div>
                              <pre className="overflow-auto rounded bg-black/30 p-2 text-xs text-white/60">
                                {JSON.stringify(t.saida, null, 2)}
                              </pre>
                            </div>
                          </div>
                        )}
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
