-- Fezinha — Migration 008: Notícias (fonte: ge.globo, via scraper)

create table if not exists public.news (
  id            bigint generated always as identity primary key,
  titulo        text not null,
  url           text not null unique,
  fonte         text not null default 'ge.globo',
  liga          text,                       -- brasileirao_serie_a | _b | null (geral)
  imagem_url    text,
  publicado_em  date,
  coletado_em   timestamptz not null default now()
);
create index if not exists idx_news_recente on public.news(publicado_em desc nulls last, coletado_em desc);

alter table public.news enable row level security;
create policy "news_leitura" on public.news for select using (auth.role() = 'authenticated');
