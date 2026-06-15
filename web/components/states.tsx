// Componentes de estado reusaveis da UI (presentacionais, sem fetch).
//
// Cobrem loading/vazio/erro + os estados de HONESTIDADE do produto:
// motor parcial, camada pendente, dado ausente, fonte vencida,
// probabilidade nao calibrada, sem recomendacao de banca.
// Nenhum texto sugere acuracia validada.

import type { ReactNode } from "react";
import type { CamadaStatus, ModoMotor } from "@/lib/types";

type Tone = "info" | "warn" | "muted" | "error";

const TONE: Record<Tone, string> = {
  info: "border-blue-500/20 bg-blue-500/10 text-blue-300",
  warn: "border-yellow-500/20 bg-yellow-500/10 text-yellow-300",
  muted: "border-white/10 bg-white/5 text-white/50",
  error: "border-red-500/20 bg-red-500/10 text-red-300",
};

export function Banner({
  tone = "info",
  titulo,
  children,
}: {
  tone?: Tone;
  titulo?: string;
  children?: ReactNode;
}) {
  return (
    <div className={`rounded border px-3 py-2 text-sm ${TONE[tone]}`}>
      {titulo && <div className="font-semibold">{titulo}</div>}
      {children && <div className={titulo ? "mt-0.5 opacity-90" : ""}>{children}</div>}
    </div>
  );
}

export function Loading({ label = "Carregando..." }: { label?: string }) {
  return <p className="text-sm text-white/60">{label}</p>;
}

export function EmptyState({ titulo = "Nada por aqui", dica }: { titulo?: string; dica?: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-fz-card p-6 text-center">
      <p className="text-white/70">{titulo}</p>
      {dica && <p className="mt-1 text-sm text-white/40">{dica}</p>}
    </div>
  );
}

export function ErrorState({ mensagem, onRetry }: { mensagem: string; onRetry?: () => void }) {
  return (
    <Banner tone="error" titulo="Algo deu errado">
      <div className="flex items-center justify-between gap-3">
        <span>{mensagem}</span>
        {onRetry && (
          <button onClick={onRetry} className="rounded bg-white/10 px-2 py-1 text-xs hover:bg-white/20">
            Tentar de novo
          </button>
        )}
      </div>
    </Banner>
  );
}

// Banner do modo do motor (estado de honestidade central).
const MODO: Record<ModoMotor, { titulo: string; desc: string; tone: Tone }> = {
  nucleo_apenas: {
    titulo: "Motor parcial",
    desc:
      "Só o núcleo estatístico está ativo — sem força individual dos times, contexto, odds ou calibração. " +
      "Jogos diferentes podem dar números parecidos.",
    tone: "warn",
  },
  modelo_only: {
    titulo: "Sem odds",
    desc: "Força real aplicada, mas sem odds nesta consulta: não há EV nem recomendação de banca.",
    tone: "info",
  },
  fallback_pesos: {
    titulo: "Fusão por pesos fixos",
    desc:
      "Agregador em modo fallback (pesos fixos, sem stacking treinado). " +
      "Probabilidades ainda não totalmente calibradas.",
    tone: "info",
  },
};

export function EngineModeBanner({ modo }: { modo?: ModoMotor }) {
  if (!modo) return null;
  const m = MODO[modo];
  return (
    <Banner tone={m.tone} titulo={m.titulo}>
      {m.desc}
    </Banner>
  );
}

// Pill de status por camada (trace).
const PILL: Record<CamadaStatus, { label: string; cls: string }> = {
  ok: { label: "ok", cls: "bg-fz-green/20 text-fz-green" },
  baseline: { label: "baseline", cls: "bg-yellow-500/20 text-yellow-300" },
  pendente: { label: "pendente", cls: "bg-white/10 text-white/40" },
  dado_ausente: { label: "dado ausente", cls: "bg-white/10 text-white/40" },
  fonte_vencida: { label: "fonte vencida", cls: "bg-orange-500/20 text-orange-300" },
  erro: { label: "erro", cls: "bg-red-500/20 text-red-300" },
};

export function LayerStatusPill({ status }: { status: CamadaStatus }) {
  const p = PILL[status];
  return <span className={`rounded px-1.5 py-0.5 text-xs ${p.cls}`}>{p.label}</span>;
}

export function MissingData({ label = "dado ausente" }: { label?: string }) {
  return <span className="text-sm italic text-white/40">— {label}</span>;
}

export function StaleSource({ fonte, desde }: { fonte: string; desde?: string }) {
  return (
    <Banner tone="warn" titulo="Fonte desatualizada">
      {fonte}
      {desde ? ` · última atualização ${desde}` : ""}. O dado pode estar vencido.
    </Banner>
  );
}

export function UncalibratedNotice() {
  return (
    <Banner tone="muted">
      Probabilidade ainda não calibrada — leitura exploratória, não validada por backtest.
    </Banner>
  );
}

export function NoBanca({ nota }: { nota?: string }) {
  return (
    <Banner tone="muted" titulo="Sem recomendação de banca">
      {nota ?? "Sem odds válidas: não há EV nem stake sugerido nesta consulta."}
    </Banner>
  );
}
