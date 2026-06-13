-- Fezinha — Migration 006: Tabelas de ingestão (fonte: API-Football)
-- match_stats (xG/posse/escanteios), player_stats (xG+xA por jogador),
-- player_status (lesão/suspensão). Mapeamento api_* para idempotência.

alter table public.teams   add column if not exists api_team_id integer;
alter table public.players add column if not exists api_player_id integer;
alter table public.matches add column if not exists api_fixture_id integer;
alter table public.matches add column if not exists arbitro text;

create table if not exists public.match_stats (
  id            bigint generated always as identity primary key,
  match_id      bigint not null references public.matches(id) on delete cascade,
  team_id       bigint not null references public.teams(id) on delete cascade,
  xg            numeric,
  posse         integer,
  escanteios    integer,
  finalizacoes  integer,
  finalizacoes_no_gol integer,
  faltas        integer,
  cartoes_amarelos integer,
  cartoes_vermelhos integer,
  atualizado_em timestamptz not null default now(),
  unique (match_id, team_id)
);

create table if not exists public.player_stats (
  id            bigint generated always as identity primary key,
  player_id     bigint not null references public.players(id) on delete cascade,
  temporada     integer not null,
  jogos         integer default 0,
  minutos       integer default 0,
  gols          integer default 0,
  assistencias  integer default 0,
  xg            numeric default 0,
  xa            numeric default 0,
  cartoes_amarelos integer default 0,
  cartoes_vermelhos integer default 0,
  atualizado_em timestamptz not null default now(),
  unique (player_id, temporada)
);

create table if not exists public.player_status (
  id            bigint generated always as identity primary key,
  player_id     bigint not null references public.players(id) on delete cascade,
  status        text not null check (status in ('ativo','lesionado','suspenso','duvida')),
  motivo        text,
  cartoes_pendurados integer default 0,
  atualizado_em timestamptz not null default now(),
  unique (player_id)
);

create index if not exists idx_match_stats_match on public.match_stats(match_id);
create index if not exists idx_player_stats_player on public.player_stats(player_id);

alter table public.match_stats   enable row level security;
alter table public.player_stats  enable row level security;
alter table public.player_status enable row level security;
create policy "match_stats_leitura"   on public.match_stats   for select using (auth.role() = 'authenticated');
create policy "player_stats_leitura"  on public.player_stats  for select using (auth.role() = 'authenticated');
create policy "player_status_leitura" on public.player_status for select using (auth.role() = 'authenticated');
