// Mocks para desenvolver a UI sem depender do engine.
//
// Espelham o output de engine/run.py por MODO do motor (nucleo_apenas /
// modelo_only / fallback_pesos). Dados sao SINTETICOS (times/placares/probs
// ficticios). Reconciliar ao contract-v0 quando o Codex entregar (tarefa #5).

import type {
  Match,
  Noticia,
  RadarEixo,
  RadarTime,
  Resultado,
  TeamDetail,
  TeamSummary,
  TraceItem,
} from "@/lib/types";

export const mockMatches: Match[] = [
  {
    id: 101,
    liga: "brasileirao_serie_a",
    data_hora: "2026-06-20T19:00:00-03:00",
    rodada: 19,
    status: "agendado",
    placar_casa: null,
    placar_fora: null,
    mandante: { nome: "Mandante FC", escudo_url: null },
    visitante: { nome: "Visitante EC", escudo_url: null },
  },
  {
    id: 102,
    liga: "brasileirao_serie_a",
    data_hora: "2026-06-21T16:00:00-03:00",
    rodada: 19,
    status: "agendado",
    placar_casa: null,
    placar_fora: null,
    mandante: { nome: "Alfa SC", escudo_url: null },
    visitante: { nome: "Beta AC", escudo_url: null },
  },
  {
    id: 90,
    liga: "brasileirao_serie_b",
    data_hora: "2026-06-14T18:30:00-03:00",
    rodada: 18,
    status: "encerrado",
    placar_casa: 2,
    placar_fora: 1,
    mandante: { nome: "Gama FC", escudo_url: null },
    visitante: { nome: "Delta EC", escudo_url: null },
  },
];

export const mockNews: Noticia[] = [
  {
    titulo: "Mandante FC confirma time titular para a rodada",
    url: "https://example.test/n/1",
    fonte: "ge.globo",
    liga: "brasileirao_serie_a",
    imagem_url: null,
    publicado_em: "2026-06-15T12:00:00-03:00",
  },
  {
    titulo: "Visitante EC tem desfalque no meio-campo",
    url: "https://example.test/n/2",
    fonte: "ge.globo",
    liga: "brasileirao_serie_a",
    imagem_url: null,
    publicado_em: "2026-06-15T09:30:00-03:00",
  },
];

// trace base reutilizado; o status muda conforme o modo
const traceNucleo: TraceItem[] = [
  { camada: "perfil_liga", topico: "Prior da liga", status: "ok", resumo: "Medias do Brasileirao.", entrada: null, saida: null },
  { camada: "pi_ratings", topico: "Forca dos times", status: "baseline", resumo: "Forca padrao (1.0) — ingestao pendente.", entrada: null, saida: null, qualidade: 1 },
  { camada: "dixon_coles", topico: "Matriz de placar", status: "ok", resumo: "1X2 / O-U / BTTS.", entrada: null, saida: null },
  { camada: "forca_comparativa", topico: "Rating transitivo", status: "pendente", resumo: "Sem historico suficiente.", entrada: null, saida: null },
  { camada: "odds", topico: "Prob implicita do mercado", status: "pendente", resumo: "Sem odds ingeridas.", entrada: null, saida: null, qualidade: 0 },
  { camada: "agregador", topico: "Fusao", status: "pendente", resumo: "Agregador real ainda nao implementado.", entrada: null, saida: null },
  { camada: "banca", topico: "EV + Kelly", status: "pendente", resumo: "Aguarda agregador + odds.", entrada: null, saida: null },
];

// MODO nucleo_apenas: sem forca individual (estado real de hoje)
export const mockResultadoNucleoApenas: Resultado = {
  partida: { mandante: "Mandante FC", visitante: "Visitante EC" },
  baseline: true,
  forca_comparativa: null,
  agregador: {
    resultado: {
      prob_casa: 0.44, prob_empate: 0.28, prob_visitante: 0.28,
      resultado_mais_provavel: "casa", placar_provavel: "1x1",
    },
    gols: { over_15: 0.74, over_25: 0.5, over_35: 0.28, btts: 0.52 },
    escanteios: { over_85: 0.6, over_95: 0.48, over_105: 0.36 },
    modo: "nucleo_apenas",
    meta: {
      modo: "nucleo_apenas",
      camadas_ativas: ["perfil_liga", "dixon_coles"],
      camadas_pendentes: ["pi_ratings", "forca_comparativa", "odds", "agregador", "banca"],
    },
  },
  indice_confianca: { valor: null, leitura: "indisponivel_ate_agregador_completo" },
  alertas: [{ tipo: "MOTOR_PARCIAL", descricao: "So nucleo estatistico ativo; sem contexto/odds/calibracao." }],
  banca: { perfil_em_uso: "moderado", recomendacoes: [], nota: "banca aguarda agregador calibrado + odds" },
  trace: traceNucleo,
};

// MODO modelo_only: forca real ingerida, mas sem odds (sem EV/banca)
export const mockResultadoModeloOnly: Resultado = {
  partida: { mandante: "Alfa SC", visitante: "Beta AC" },
  baseline: false,
  forca_comparativa: {
    mandante: { ifc: 63, leitura: "forte" },
    visitante: { ifc: 47, leitura: "media" },
    diferenca_ifc: 16,
    expectativa_mandante: 0.62,
    leitura: "vantagem_casa",
    adversarios_comuns: [
      { adversario: "Gama FC", resultado_mandante: "venceu 2x0 (casa)", resultado_visitante: "empatou 1x1 (fora)" },
    ],
    jogos_no_grafo: 174,
  },
  agregador: {
    resultado: {
      prob_casa: 0.55, prob_empate: 0.24, prob_visitante: 0.21,
      resultado_mais_provavel: "casa", placar_provavel: "2x1",
    },
    gols: { over_15: 0.78, over_25: 0.54, over_35: 0.31, btts: 0.56 },
    escanteios: { over_85: 0.62, over_95: 0.5, over_105: 0.38 },
    modo: "modelo_only",
    meta: {
      modo: "modelo_only",
      camadas_ativas: ["perfil_liga", "pi_ratings", "dixon_coles", "forca_comparativa"],
      camadas_pendentes: ["odds", "agregador", "banca"],
    },
  },
  indice_confianca: { valor: 0.55, leitura: "media" },
  alertas: [{ tipo: "SEM_ODDS", descricao: "Sem odds ingeridas: sem EV/banca nesta consulta." }],
  banca: { perfil_em_uso: "moderado", recomendacoes: [], nota: "sem odds: sem EV/banca" },
  trace: traceNucleo.map((t) =>
    t.camada === "pi_ratings"
      ? { ...t, status: "ok", resumo: "Forca real (174 jogos).", qualidade: 4 }
      : t.camada === "forca_comparativa"
        ? { ...t, status: "ok", resumo: "IFC do grafo da liga." }
        : t,
  ),
};

// MODO fallback_pesos: com odds -> EV/banca via pesos fixos (sem stacking)
export const mockResultadoFallbackPesos: Resultado = {
  partida: { mandante: "Alfa SC", visitante: "Beta AC" },
  baseline: false,
  forca_comparativa: mockResultadoModeloOnly.forca_comparativa,
  agregador: {
    resultado: {
      prob_casa: 0.57, prob_empate: 0.23, prob_visitante: 0.2,
      resultado_mais_provavel: "casa", placar_provavel: "2x1",
    },
    gols: { over_15: 0.8, over_25: 0.58, over_35: 0.33, btts: 0.57 },
    escanteios: { over_85: 0.63, over_95: 0.51, over_105: 0.39 },
    modo: "fallback_pesos",
    meta: {
      modo: "fallback_pesos",
      camadas_ativas: ["perfil_liga", "pi_ratings", "dixon_coles", "forca_comparativa", "odds", "agregador", "banca"],
      camadas_pendentes: [],
      pesos_em_uso: { modelo_proprio: 0.55, odds: 0.3, consenso: 0.15 },
      data_ultimo_treino: null,
    },
  },
  indice_confianca: { valor: 0.7, leitura: "media_alta" },
  alertas: [],
  banca: {
    perfil_em_uso: "moderado",
    recomendacoes: [
      {
        mercado: "over_under_gols", selecao: "Over 2.5",
        prob_modelo: 0.58, odd: 1.95, ev: 0.131,
        stake_sugerido: 0.03, confianca: 0.7, decisao: "apostar",
      },
    ],
    nota: "fallback por pesos fixos (sem stacking treinado)",
  },
  trace: mockResultadoModeloOnly.trace?.map((t) =>
    t.camada === "odds"
      ? { ...t, status: "ok", resumo: "Prob implicita (2 casas).", qualidade: 3 }
      : t.camada === "agregador"
        ? { ...t, status: "ok", resumo: "Fusao por pesos fixos." }
        : t.camada === "banca"
          ? { ...t, status: "ok", resumo: "EV + 1/2 Kelly." }
          : t,
  ),
};

export const mockResultadoPorModo = {
  nucleo_apenas: mockResultadoNucleoApenas,
  modelo_only: mockResultadoModeloOnly,
  fallback_pesos: mockResultadoFallbackPesos,
} as const;

// --- Seção de times (mock) ---

const REF = { liga: "brasileirao_a", temporada: 2026 };

function eixo(
  id: string,
  label: string,
  base: number,
  atual: number,
  janela = "ultimos_10",
  qualidade = 4,
): RadarEixo {
  return {
    id,
    label,
    base,
    atual,
    delta: atual - base,
    valor_bruto: atual,
    qualidade,
    status: "ok",
    janela,
    referencia: REF,
    fontes: ["CBF resultados"],
  };
}

const eixoDisciplina: RadarEixo = {
  id: "controle_disciplinar",
  label: "Disciplina",
  base: null,
  atual: null,
  delta: null,
  valor_bruto: null,
  qualidade: 0,
  status: "dado_ausente",
  janela: "temporada",
  referencia: REF,
  fontes: [],
  motivo_ausencia: "CA/CV ainda nao ingeridos da CBF",
};

export function mockRadarTime(
  time: { id: number; nome: string; escudo_url: string | null },
  contexto: "casa" | "fora" | "neutro" = "neutro",
): RadarTime {
  return {
    modo: "resultado",
    escala: { min: 0, max: 100 },
    time,
    contexto,
    eixos: [
      eixo("forca_ofensiva", "Ataque", 72, 78),
      eixo("solidez_defensiva", "Defesa", 64, 60),
      eixo("forma_recente", "Forma", 70, 82, "ultimos_5"),
      eixo("consistencia", "Consistência", 55, 52),
      eixo("contexto_casa_fora", contexto === "fora" ? "Fora" : "Casa", 68, 74),
      eixoDisciplina,
    ],
    modificadores: [],
    sinais: ["pico"],
  };
}

export const mockTeams: TeamSummary[] = [
  { id: 1, nome: "Alfa SC", escudo_url: null, liga: "brasileirao_serie_a", posicao: 3, pontos: 34, forma: ["V", "V", "E", "D", "V"] },
  { id: 2, nome: "Beta AC", escudo_url: null, liga: "brasileirao_serie_a", posicao: 11, pontos: 22, forma: ["D", "E", "V", "D", "E"] },
  { id: 3, nome: "Gama FC", escudo_url: null, liga: "brasileirao_serie_b", posicao: 5, pontos: 30, forma: ["V", "D", "V", "V", "E"] },
];

export const mockTeamDetail: TeamDetail = {
  resumo: mockTeams[0],
  radar: mockRadarTime({ id: 1, nome: "Alfa SC", escudo_url: null }, "casa"),
  estatisticas: [
    { label: "Gols pró/jogo", valor: "1.7", qualidade: 4 },
    { label: "Gols contra/jogo", valor: "0.9", qualidade: 4 },
    { label: "IFC", valor: "63", qualidade: 4 },
    { label: "Saldo", valor: "+12", qualidade: 4 },
    { label: "Over 2.5 (jogos)", valor: "56%", qualidade: 3 },
    { label: "Aproveitamento", valor: "63%", qualidade: 4 },
  ],
  elenco: [],
  elenco_disponivel: false,
  proximos: mockMatches.filter(
    (m) => m.mandante?.nome === "Alfa SC" || m.visitante?.nome === "Alfa SC",
  ),
  ultimos: [],
  noticias: mockNews,
  noticias_filtro_aproximado: true,
};
