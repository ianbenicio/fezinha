-- Fezinha — Seed 003: Times da Série B 2026
-- Fonte: Wikipedia (Campeonato Brasileiro 2026 - Série B).
-- Idempotente (on conflict slug).

insert into public.teams (nome, slug, liga, caracteristicas) values
  ('América-MG',    'america-mg',   'brasileirao_serie_b', '{"cidade":"Belo Horizonte","estado":"MG"}'),
  ('Athletic',      'athletic',     'brasileirao_serie_b', '{"cidade":"São João del-Rei","estado":"MG"}'),
  ('Atlético-GO',   'atletico-go',  'brasileirao_serie_b', '{"cidade":"Goiânia","estado":"GO"}'),
  ('Avaí',          'avai',         'brasileirao_serie_b', '{"cidade":"Florianópolis","estado":"SC"}'),
  ('Botafogo-SP',   'botafogo-sp',  'brasileirao_serie_b', '{"cidade":"Ribeirão Preto","estado":"SP"}'),
  ('Ceará',         'ceara',        'brasileirao_serie_b', '{"cidade":"Fortaleza","estado":"CE"}'),
  ('CRB',           'crb',          'brasileirao_serie_b', '{"cidade":"Maceió","estado":"AL"}'),
  ('Criciúma',      'criciuma',     'brasileirao_serie_b', '{"cidade":"Criciúma","estado":"SC"}'),
  ('Cuiabá',        'cuiaba',       'brasileirao_serie_b', '{"cidade":"Cuiabá","estado":"MT"}'),
  ('Fortaleza',     'fortaleza',    'brasileirao_serie_b', '{"cidade":"Fortaleza","estado":"CE"}'),
  ('Goiás',         'goias',        'brasileirao_serie_b', '{"cidade":"Goiânia","estado":"GO"}'),
  ('Juventude',     'juventude',    'brasileirao_serie_b', '{"cidade":"Caxias do Sul","estado":"RS"}'),
  ('Londrina',      'londrina',     'brasileirao_serie_b', '{"cidade":"Londrina","estado":"PR"}'),
  ('Náutico',       'nautico',      'brasileirao_serie_b', '{"cidade":"Recife","estado":"PE"}'),
  ('Novorizontino', 'novorizontino','brasileirao_serie_b', '{"cidade":"Novo Horizonte","estado":"SP"}'),
  ('Operário-PR',   'operario-pr',  'brasileirao_serie_b', '{"cidade":"Ponta Grossa","estado":"PR"}'),
  ('Ponte Preta',   'ponte-preta',  'brasileirao_serie_b', '{"cidade":"Campinas","estado":"SP"}'),
  ('São Bernardo',  'sao-bernardo', 'brasileirao_serie_b', '{"cidade":"São Bernardo do Campo","estado":"SP"}'),
  ('Sport',         'sport',        'brasileirao_serie_b', '{"cidade":"Recife","estado":"PE"}'),
  ('Vila Nova',     'vila-nova',    'brasileirao_serie_b', '{"cidade":"Goiânia","estado":"GO"}')
on conflict (slug) do nothing;

-- NOTA: as partidas (matches) das séries A e B nesta fase são EXEMPLOS
-- (confrontos/datas plausíveis) até a ingestão do calendário oficial.
