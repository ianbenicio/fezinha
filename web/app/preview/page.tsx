// Pagina de DEV (/preview). Renderiza os componentes de estado com o mock
// (web/lib/mock.ts), sem depender do engine. Util para revisar UX de incerteza.
// Remover ou proteger por flag antes de producao.

import {
  EngineModeBanner,
  EmptyState,
  ErrorState,
  LayerStatusPill,
  Loading,
  MissingData,
  NoBanca,
  StaleSource,
  UncalibratedNotice,
} from "@/components/states";
import { mockResultadoPorModo } from "@/lib/mock";
import type { ModoMotor } from "@/lib/types";

const MODOS: ModoMotor[] = ["nucleo_apenas", "modelo_only", "fallback_pesos"];

export default function PreviewPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-bold">Preview — estados de UI</h1>
        <p className="text-sm text-white/40">
          Página de dev. Renderiza os componentes de estado com mock
          (<code>web/lib/mock.ts</code>). Não usa o engine.
        </p>
      </div>

      <section className="space-y-3">
        <h2 className="font-semibold">Genéricos</h2>
        <Loading />
        <EmptyState titulo="Nenhum jogo neste período" dica="Use os controles para navegar." />
        <ErrorState mensagem="Falha ao carregar (exemplo)." />
      </section>

      <section className="space-y-3">
        <h2 className="font-semibold">Modo do motor</h2>
        {MODOS.map((m) => (
          <EngineModeBanner key={m} modo={m} />
        ))}
      </section>

      <section className="space-y-3">
        <h2 className="font-semibold">Honestidade</h2>
        <UncalibratedNotice />
        <NoBanca />
        <StaleSource fonte="ge.globo" desde="14/06" />
        <div className="flex items-center gap-2 text-sm text-white/60">
          camada: <LayerStatusPill status="ok" /> <LayerStatusPill status="baseline" />{" "}
          <LayerStatusPill status="pendente" />
        </div>
        <div className="text-sm text-white/60">
          escalação confirmada: <MissingData label="escalação ausente" />
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="font-semibold">Por modo (mock)</h2>
        {MODOS.map((m) => {
          const r = mockResultadoPorModo[m];
          return (
            <div key={m} className="space-y-2 rounded-lg bg-fz-card p-4">
              <div className="text-sm text-white/50">
                {m} — {r.partida?.mandante} x {r.partida?.visitante}
              </div>
              <EngineModeBanner modo={r.agregador?.modo} />
              {r.banca && r.banca.recomendacoes.length === 0 && <NoBanca nota={r.banca.nota} />}
              {r.indice_confianca?.valor == null && <UncalibratedNotice />}
            </div>
          );
        })}
      </section>
    </div>
  );
}
