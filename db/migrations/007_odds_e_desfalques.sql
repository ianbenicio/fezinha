-- Fezinha — Migration 007: Odds + desfalques (entrada manual)
-- Dados que o ge não fornece; preenchidos via template por rodada.

create table if not exists public.odds (
  id            bigint generated always as identity primary key,
  match_id      bigint not null references public.matches(id) on delete cascade,
  mercado       text not null,        -- '1x2' | 'over_under_gols' | 'escanteios'
  selecao       text not null,        -- 'casa'|'empate'|'visitante'|'over_2.5'|...
  valor         numeric not null,
  casa_aposta   text,
  capturado_em  timestamptz not null default now()
);
create index if not exists idx_odds_match on public.odds(match_id, mercado);

alter table public.odds enable row level security;
create policy "odds_leitura" on public.odds for select using (auth.role() = 'authenticated');

-- formato: [{"time":"casa|fora","jogador":"...","motivo":"lesao|suspensao|duvida"}]
alter table public.matches add column if not exists desfalques jsonb not null default '[]'::jsonb;
