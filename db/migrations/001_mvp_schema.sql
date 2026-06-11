-- Fezinha — Migration 001: MVP Schema
-- Áreas: Auth+Créditos · Consulta+Histórico · Catálogo (Série A)
-- Aplicar em projeto Supabase DEDICADO ao Fezinha (NÃO no projeto acadêmico).
-- Auth: usa auth.users do Supabase. RLS em tudo.

-- ════════════════════════════════════════════════════════
-- AUTH + PERFIL
-- ════════════════════════════════════════════════════════

create table public.profiles (
  id            uuid primary key references auth.users(id) on delete cascade,
  email         text not null,
  nome          text,
  perfil_risco  text not null default 'moderado'
                check (perfil_risco in ('conservador','moderado','agressivo')),
  preferencias  jsonb not null default '{}'::jsonb,  -- filtros de feed, times favoritos
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "perfil_proprio_select" on public.profiles
  for select using (auth.uid() = id);
create policy "perfil_proprio_update" on public.profiles
  for update using (auth.uid() = id);

-- ════════════════════════════════════════════════════════
-- CRÉDITOS
-- ════════════════════════════════════════════════════════

create table public.credit_balance (
  user_id    uuid primary key references public.profiles(id) on delete cascade,
  saldo      integer not null default 0 check (saldo >= 0),
  updated_at timestamptz not null default now()
);

alter table public.credit_balance enable row level security;
create policy "saldo_proprio_select" on public.credit_balance
  for select using (auth.uid() = user_id);
-- escrita só via service_role (backend) — sem policy de update p/ usuário

create table public.credit_transactions (
  id         bigint generated always as identity primary key,
  user_id    uuid not null references public.profiles(id) on delete cascade,
  tipo       text not null check (tipo in ('compra','gasto','bonus','ajuste','estorno')),
  valor      integer not null,            -- positivo crédito, negativo débito
  motivo     text,
  query_id   bigint,                      -- FK lógica p/ queries (gasto)
  created_at timestamptz not null default now()
);

alter table public.credit_transactions enable row level security;
create policy "transacoes_proprias_select" on public.credit_transactions
  for select using (auth.uid() = user_id);

create index idx_credit_tx_user on public.credit_transactions(user_id, created_at desc);

-- ════════════════════════════════════════════════════════
-- CATÁLOGO (Série A) — leitura pública, escrita via ingestão (service_role)
-- ════════════════════════════════════════════════════════

create table public.teams (
  id               bigint generated always as identity primary key,
  nome             text not null,
  slug             text unique not null,
  liga             text not null default 'brasileirao_serie_a',
  escudo_url       text,
  descricao        text,
  caracteristicas  jsonb not null default '{}'::jsonb,  -- estilo, PPDA médio, fator casa...
  atualizado_em    timestamptz not null default now()
);

create table public.players (
  id               bigint generated always as identity primary key,
  team_id          bigint not null references public.teams(id) on delete cascade,
  nome             text not null,
  posicao          text,
  descricao        text,
  caracteristicas  jsonb not null default '{}'::jsonb,  -- xG+xA/90, papel, contribuição
  status           text default 'ativo'
                   check (status in ('ativo','lesionado','suspenso','duvida')),
  atualizado_em    timestamptz not null default now()
);

create index idx_players_team on public.players(team_id);

create table public.matches (
  id            bigint generated always as identity primary key,
  liga          text not null default 'brasileirao_serie_a',
  home_team_id  bigint not null references public.teams(id),
  away_team_id  bigint not null references public.teams(id),
  data_hora     timestamptz not null,
  rodada        integer,
  status        text not null default 'agendado'
                check (status in ('agendado','ao_vivo','encerrado','adiado')),
  placar_casa   integer,
  placar_fora   integer,
  created_at    timestamptz not null default now()
);

create index idx_matches_data on public.matches(data_hora);

-- catálogo: leitura pública (qualquer autenticado)
alter table public.teams   enable row level security;
alter table public.players enable row level security;
alter table public.matches enable row level security;
create policy "teams_leitura"   on public.teams   for select using (auth.role() = 'authenticated');
create policy "players_leitura" on public.players for select using (auth.role() = 'authenticated');
create policy "matches_leitura" on public.matches for select using (auth.role() = 'authenticated');

-- ════════════════════════════════════════════════════════
-- CONSULTA + HISTÓRICO
-- ════════════════════════════════════════════════════════

create table public.queries (
  id              bigint generated always as identity primary key,
  user_id         uuid not null references public.profiles(id) on delete cascade,
  match_id        bigint references public.matches(id),
  complexidade    text not null check (complexidade in ('simples','padrao','premium')),
  custo_creditos  integer not null,
  mercados        text[] not null default '{}',   -- ['1x2','over_under','escanteios']
  resultado       jsonb,                            -- saída do motor (prob, confiança, recomendação)
  status          text not null default 'processando'
                  check (status in ('processando','concluida','erro')),
  created_at      timestamptz not null default now()
);

alter table public.queries enable row level security;
create policy "queries_proprias_select" on public.queries
  for select using (auth.uid() = user_id);
create policy "queries_proprias_insert" on public.queries
  for insert with check (auth.uid() = user_id);

create index idx_queries_user on public.queries(user_id, created_at desc);

-- ════════════════════════════════════════════════════════
-- TRIGGER: cria profile + saldo inicial ao registrar usuário
-- ════════════════════════════════════════════════════════

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, email, nome)
    values (new.id, new.email, new.raw_user_meta_data->>'nome');
  insert into public.credit_balance (user_id, saldo)
    values (new.id, 10);  -- 10 créditos de boas-vindas (configurável)
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
