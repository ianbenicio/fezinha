// Tipos do contrato engine -> api -> web (lado consumidor).
//
// Baseline = output atual de engine/run.py (ver docs/web-map.md).
// Campos marcados "contract-v0 (previsto)" antecipam
// docs/contract-v0-requirements-web.md e serao reconciliados na revisao do
// contrato (tarefa #5). Nao renomear os campos ja consumidos por /consulta.

export type Liga = "brasileirao_serie_a" | "brasileirao_serie_b";

export type TeamRef = { nome: string; escudo_url?: string | null };

export type MatchStatus = "agendado" | "ao_vivo" | "encerrado" | "adiado";

export type Match = {
  id: number;
  liga: string;
  data_hora: string | null;
  rodada: number | null;
  status: string;
  placar_casa?: number | null;
  placar_fora?: number | null;
  mandante: TeamRef | null;
  visitante: TeamRef | null;
};

export type Partida = {
  data_hora: string;
  rodada: number | null;
  status: string;
  local?: string;
  mandante: TeamRef | null;
  visitante: TeamRef | null;
};

export type Noticia = {
  titulo: string;
  url: string;
  fonte: string;
  liga?: string | null;
  imagem_url?: string | null;
  publicado_em?: string | null;
};

export type Consulta = {
  id: number;
  match_id: number;
  complexidade: string;
  custo_creditos: number;
  mercados: string[];
  status: string;
  created_at: string;
};

// --- Saida do motor (Resultado) ---

// status por camada no trace (contract-v0 §9)
export type CamadaStatus =
  | "ok"
  | "baseline"
  | "pendente"
  | "dado_ausente"
  | "fonte_vencida"
  | "erro";

export type TraceItem = {
  camada: string;
  topico: string;
  status: CamadaStatus;
  resumo?: string;
  justificativa?: string;
  fonte?: string;
  fonte_ausente?: string;
  entrada: unknown;
  saida: unknown;
  qualidade?: number; // 0..5
};

export type ForcaComparativa = {
  mandante: { ifc: number; leitura: string };
  visitante: { ifc: number; leitura: string };
  diferenca_ifc: number;
  expectativa_mandante: number;
  leitura: string;
  adversarios_comuns: {
    adversario: string;
    resultado_mandante: string;
    resultado_visitante: string;
  }[];
  ajustes_aplicados?: string[];
  jogos_no_grafo: number;
};

export type AgregadorResultado = {
  prob_casa: number;
  prob_empate: number;
  prob_visitante: number;
  resultado_mais_provavel: string;
  placar_provavel: string;
  top3_placares?: unknown[];
};
export type AgregadorGols = {
  over_05?: number;
  over_15: number;
  over_25: number;
  over_35: number;
  btts: number;
};
export type AgregadorEscanteios = {
  over_85: number;
  over_95: number;
  over_105: number;
};

// modo do motor (contract-v0 §4.1). Canonico em agregador.modo; espelhado em meta.modo.
export type ModoMotor = "nucleo_apenas" | "modelo_only" | "fallback_pesos";

export type AgregadorMeta = {
  modo: ModoMotor;
  camadas_ativas: string[];
  camadas_pendentes: string[];
  pesos_em_uso?: Record<string, number>;
  data_ultimo_treino?: string | null;
};

export type Agregador = {
  modo: ModoMotor;
  resultado: AgregadorResultado;
  gols: AgregadorGols;
  escanteios: AgregadorEscanteios;
  meta: AgregadorMeta;
};

// engine ja emite os 3 abaixo; web passa a renderizar (folga, sem breaking change)
export type IndiceConfianca = { valor: number | null; leitura: string };

export type Alerta = {
  tipo: string;
  descricao: string;
  severidade?: "info" | "aviso" | "bloqueio";
};

export type BancaRec = {
  mercado: string;
  selecao: string;
  prob_modelo: number;
  odd: number;
  ev: number;
  stake_sugerido: number;
  confianca: number;
  decisao: "apostar" | "evitar" | "aguardar_escalacao";
};
export type Banca = {
  perfil_em_uso: string;
  recomendacoes: BancaRec[];
  nota?: string; // ex: "sem odds: sem EV/banca"
};

export type Lambdas = { casa: number; fora: number; escanteios: number };

export type Resultado = {
  _stub?: boolean;
  fonte?: string;
  complexidade?: string;
  mercados?: string[];
  partida?: { mandante: string; visitante: string };
  baseline?: boolean;
  lambdas?: Lambdas;
  forca_comparativa?: ForcaComparativa | null;
  agregador?: Agregador;
  indice_confianca?: IndiceConfianca;
  alertas?: Alerta[];
  banca?: Banca;
  trace?: TraceItem[];
};

// --- Seção de times (radar + detalhe). Mock-first; ver docs/ux/team-section.md ---

export type RadarEixoId =
  | "forca_ofensiva"
  | "solidez_defensiva"
  | "forma_recente"
  | "consistencia"
  | "contexto_casa_fora"
  | "controle_disciplinar";

export type RadarEixo = {
  id: RadarEixoId | string;
  label: string;
  base: number | null;
  atual: number | null;
  delta: number | null;
  valor_bruto: number | null;
  qualidade: number; // 0-5
  status: CamadaStatus;
  janela: string;
  referencia: { liga: string; temporada: number };
  fontes: string[];
  motivo_ausencia?: string;
};

export type RadarModificador = {
  eixo: string;
  delta: number;
  motivo: string;
  fonte: string;
  validade?: string;
};

export type RadarSinal = "pico" | "crise" | "volatilidade" | "alerta_disciplina";

export type RadarTime = {
  modo: "resultado";
  escala: { min: number; max: number };
  time: { id: number; nome: string; escudo_url: string | null };
  contexto: "casa" | "fora" | "neutro";
  eixos: RadarEixo[];
  modificadores: RadarModificador[];
  sinais: RadarSinal[];
};

export type ResultadoForma = "V" | "E" | "D";

export type TeamSummary = {
  id: number;
  nome: string;
  escudo_url: string | null;
  liga: string;
  posicao?: number | null;
  pontos?: number | null;
  forma?: ResultadoForma[];
};

export type TeamStat = { label: string; valor: string; qualidade?: number };

export type Jogador = {
  nome: string;
  posicao: string;
  jogos?: number;
  gols?: number;
  status?: "disponivel" | "lesionado" | "suspenso" | "duvida";
};

export type TeamDetail = {
  resumo: TeamSummary;
  radar?: RadarTime;
  estatisticas: TeamStat[];
  elenco: Jogador[];
  elenco_disponivel: boolean; // false → placeholder honesto
  proximos: Match[];
  ultimos: Match[];
  noticias: Noticia[];
  noticias_filtro_aproximado?: boolean;
};
