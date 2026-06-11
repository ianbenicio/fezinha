-- Fezinha — Seed 001: Times da Série A 2026
-- Fonte: Wikipedia (Campeonato Brasileiro 2026 - Série A).
-- Idempotente (on conflict slug). caracteristicas preenchidas pela ingestão depois.

insert into public.teams (nome, slug, liga, caracteristicas) values
  ('Athletico Paranaense', 'athletico-pr', 'brasileirao_serie_a', '{"cidade":"Curitiba","estado":"PR"}'),
  ('Atlético Mineiro',     'atletico-mg',  'brasileirao_serie_a', '{"cidade":"Belo Horizonte","estado":"MG"}'),
  ('Bahia',                'bahia',        'brasileirao_serie_a', '{"cidade":"Salvador","estado":"BA"}'),
  ('Botafogo',             'botafogo',     'brasileirao_serie_a', '{"cidade":"Rio de Janeiro","estado":"RJ"}'),
  ('Chapecoense',          'chapecoense',  'brasileirao_serie_a', '{"cidade":"Chapecó","estado":"SC"}'),
  ('Corinthians',          'corinthians',  'brasileirao_serie_a', '{"cidade":"São Paulo","estado":"SP"}'),
  ('Coritiba',             'coritiba',     'brasileirao_serie_a', '{"cidade":"Curitiba","estado":"PR"}'),
  ('Cruzeiro',             'cruzeiro',     'brasileirao_serie_a', '{"cidade":"Belo Horizonte","estado":"MG"}'),
  ('Flamengo',             'flamengo',     'brasileirao_serie_a', '{"cidade":"Rio de Janeiro","estado":"RJ"}'),
  ('Fluminense',           'fluminense',   'brasileirao_serie_a', '{"cidade":"Rio de Janeiro","estado":"RJ"}'),
  ('Grêmio',               'gremio',       'brasileirao_serie_a', '{"cidade":"Porto Alegre","estado":"RS"}'),
  ('Internacional',        'internacional','brasileirao_serie_a', '{"cidade":"Porto Alegre","estado":"RS"}'),
  ('Mirassol',             'mirassol',     'brasileirao_serie_a', '{"cidade":"Mirassol","estado":"SP"}'),
  ('Palmeiras',            'palmeiras',    'brasileirao_serie_a', '{"cidade":"São Paulo","estado":"SP"}'),
  ('Red Bull Bragantino',  'bragantino',   'brasileirao_serie_a', '{"cidade":"Bragança Paulista","estado":"SP"}'),
  ('Remo',                 'remo',         'brasileirao_serie_a', '{"cidade":"Belém","estado":"PA"}'),
  ('Santos',               'santos',       'brasileirao_serie_a', '{"cidade":"Santos","estado":"SP"}'),
  ('São Paulo',            'sao-paulo',    'brasileirao_serie_a', '{"cidade":"São Paulo","estado":"SP"}'),
  ('Vasco da Gama',        'vasco',        'brasileirao_serie_a', '{"cidade":"Rio de Janeiro","estado":"RJ"}'),
  ('Vitória',              'vitoria',      'brasileirao_serie_a', '{"cidade":"Salvador","estado":"BA"}')
on conflict (slug) do nothing;
