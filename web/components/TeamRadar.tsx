// Radar do time (SVG puro, sem lib de chart).
// Desenha perfil (base, tracejado) vs momento (atual, solido). Eixos sem dado
// (status != ok) ficam apagados, valor tratado como 0, com tooltip de ausencia.
// Exploratorio/explicativo — nao e probabilidade.

import type { RadarEixo, RadarTime } from "@/lib/types";

const SIZE = 280;
const C = SIZE / 2;
const R = 100;
const RINGS = [0.25, 0.5, 0.75, 1];

function pt(i: number, n: number, raio: number): [number, number] {
  const ang = ((360 / n) * i - 90) * (Math.PI / 180);
  return [C + raio * Math.cos(ang), C + raio * Math.sin(ang)];
}

function ausente(e: RadarEixo): boolean {
  return e.status !== "ok" || e.atual == null;
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

function tooltip(e: RadarEixo): string {
  if (ausente(e)) return `${e.label}: ${e.motivo_ausencia ?? "sem dado"}`;
  return `${e.label} — base ${e.base} · atual ${e.atual} · ${e.janela} · qualidade ${e.qualidade}/5 · ${e.fontes.join(", ")}`;
}

export function TeamRadar({ radar }: { radar: RadarTime }) {
  const n = radar.eixos.length;
  return (
    <div className="rounded-lg bg-fz-card p-4">
      <div className="mb-1 flex items-baseline justify-between">
        <h2 className="font-semibold">Radar — {radar.time.nome}</h2>
        <span className="text-xs text-white/40">exploratório · não validado</span>
      </div>
      <p className="mb-2 text-xs text-white/40">
        <span className="text-fz-green">●</span> momento (atual) ·{" "}
        <span className="text-blue-400">┄</span> perfil (base)
      </p>

      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="mx-auto block w-full max-w-[320px]">
        {RINGS.map((g, gi) => (
          <polygon
            key={gi}
            points={radar.eixos.map((_, i) => pt(i, n, R * g).join(",")).join(" ")}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
          />
        ))}

        {radar.eixos.map((e, i) => {
          const [ex, ey] = pt(i, n, R);
          const [lx, ly] = pt(i, n, R + 18);
          const off = ausente(e);
          return (
            <g key={e.id}>
              <line x1={C} y1={C} x2={ex} y2={ey} stroke="rgba(255,255,255,0.08)" />
              <text
                x={lx}
                y={ly}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="9"
                className={off ? "fill-white/25" : "fill-white/55"}
              >
                {e.label}
                {off ? " ⚠" : ""}
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
      </svg>

      {radar.sinais.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {radar.sinais.map((s) => (
            <span key={s} className="rounded bg-fz-green/20 px-1.5 py-0.5 text-xs text-fz-green">
              {s}
            </span>
          ))}
        </div>
      )}
      <p className="mt-2 text-xs text-white/30">Passe o mouse nos eixos para base, fonte e qualidade.</p>
    </div>
  );
}
