// Radar do time (SVG puro, sem lib de chart). Consome radar_time_v0.
// Desenha perfil (base, tracejado) vs momento (atual, solido).
// - dado_ausente / atual==null: eixo apagado, valor tratado como 0, tooltip de ausencia.
// - baixa_amostra / quarentena / conflito / fonte_vencida: valor EXIBIDO com ressalva (ambar).
// Exploratorio/explicativo — nao e probabilidade (meta.entra_no_agregador: false).

import type { RadarEixo, RadarTime } from "@/lib/types";

const SIZE = 280;
const C = SIZE / 2;
const R = 100;
const RINGS = [0.25, 0.5, 0.75, 1];

// status com valor exibivel, mas que merece ressalva visual
const AVISO = new Set(["baixa_amostra", "quarentena", "conflito", "fonte_vencida"]);

function pt(i: number, n: number, raio: number): [number, number] {
  const ang = ((360 / n) * i - 90) * (Math.PI / 180);
  return [C + raio * Math.cos(ang), C + raio * Math.sin(ang)];
}

// ausente = sem valor desenhavel (nao contribui para o poligono)
function ausente(e: RadarEixo): boolean {
  return e.atual == null || e.status === "dado_ausente";
}

// aviso = tem valor, mas com ressalva de amostra/qualidade
function aviso(e: RadarEixo): boolean {
  return !ausente(e) && AVISO.has(e.status);
}

function poligono(eixos: RadarEixo[], pick: (e: RadarEixo) => number | null): string {
  return eixos
    .map((e, i) => {
      const v = pick(e);
      const r = v == null ? 0 : (Math.max(0, Math.min(100, v)) / 100) * R;
      const [x, y] = pt(i, eixos.length, r);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

function fontesTxt(e: RadarEixo): string {
  return e.fontes.length ? e.fontes.map((f) => f.source_id).join(", ") : "sem fonte";
}

function tooltip(e: RadarEixo): string {
  if (ausente(e)) return `${e.label}: ${e.motivo_ausencia ?? e.status}`;
  const ressalva = aviso(e) ? ` · ${e.status}` : "";
  return `${e.label} — base ${e.base} · atual ${e.atual} · Δ ${e.delta ?? 0} · ${e.janela.jogos} jogos (${e.janela.tipo}) · qualidade ${e.qualidade} · ${fontesTxt(e)}${ressalva}`;
}

export function TeamRadar({ radar }: { radar: RadarTime }) {
  const n = radar.eixos.length;
  const temAviso = radar.eixos.some(aviso);
  const temAusente = radar.eixos.some(ausente);

  return (
    <div className="rounded-lg bg-fz-card p-4">
      <div className="mb-1 flex items-baseline justify-between">
        <h2 className="font-semibold">Radar — {radar.team.nome}</h2>
        <span className="text-xs text-white/40">exploratório · não validado</span>
      </div>
      <p className="mb-2 text-xs text-white/40">
        <span className="text-fz-green">●</span> momento (atual) ·{" "}
        <span className="text-blue-400">┄</span> perfil (base)
      </p>

      {/* viewBox com folga lateral: labels ancoradas por lado nao clipam */}
      <svg viewBox={`-44 0 ${SIZE + 88} ${SIZE}`} className="mx-auto block w-full max-w-[360px]">
        {RINGS.map((g, gi) => (
          <polygon
            key={gi}
            points={radar.eixos.map((_, i) => pt(i, n, R * g).join(",")).join(" ")}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
          />
        ))}

        {radar.eixos.map((e, i) => {
          const cos = Math.cos(((360 / n) * i - 90) * (Math.PI / 180));
          const [ex, ey] = pt(i, n, R);
          const [lx, ly] = pt(i, n, R + 14);
          const off = ausente(e);
          const warn = aviso(e);
          const anchor = Math.abs(cos) < 0.3 ? "middle" : cos > 0 ? "start" : "end";
          const cls = off ? "fill-white/25" : warn ? "fill-amber-300/80" : "fill-white/55";
          return (
            <g key={e.id}>
              <line x1={C} y1={C} x2={ex} y2={ey} stroke="rgba(255,255,255,0.08)" />
              <text
                x={lx}
                y={ly}
                textAnchor={anchor}
                dominantBaseline="middle"
                fontSize="9"
                className={cls}
              >
                {e.label}
                {off ? " ⚠" : warn ? " *" : ""}
                <title>{tooltip(e)}</title>
              </text>
            </g>
          );
        })}

        {/* perfil (base) */}
        <polygon
          points={poligono(radar.eixos, (e) => e.base)}
          fill="rgba(59,130,246,0.10)"
          stroke="rgba(59,130,246,0.55)"
          strokeDasharray="4 3"
        />
        {/* momento (atual) */}
        <polygon
          points={poligono(radar.eixos, (e) => e.atual)}
          fill="rgba(34,197,94,0.18)"
          stroke="#22c55e"
        />

        {/* marcadores de vertice: verde (ok) / ambar (aviso) — eixos com dado */}
        {radar.eixos.map((e, i) => {
          if (ausente(e)) return null;
          const r = (Math.max(0, Math.min(100, e.atual as number)) / 100) * R;
          const [x, y] = pt(i, n, r);
          return <circle key={e.id} cx={x} cy={y} r={2.6} fill={aviso(e) ? "#f59e0b" : "#22c55e"} />;
        })}
      </svg>

      {(temAusente || temAviso) && (
        <p className="mt-2 text-xs text-white/40">
          {temAusente && (
            <span>
              <span className="text-white/25">⚠ apagado</span> = dado ausente.{" "}
            </span>
          )}
          {temAviso && (
            <span>
              <span className="text-amber-300/80">* âmbar</span> = baixa amostra/qualidade (valor com ressalva).
            </span>
          )}
        </p>
      )}
      <p className="mt-1 text-xs text-white/30">
        Passe o mouse nos eixos para base, fonte, janela e qualidade.
      </p>
    </div>
  );
}
