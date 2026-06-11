-- Fezinha — Seed 002: Partidas de EXEMPLO (teste do fluxo)
-- ATENÇÃO: confrontos/datas fictícios para testar a consulta ponta-a-ponta.
-- NÃO é o calendário oficial — substituir pela ingestão do calendário real.
-- IDs de time conforme seed 001 (ordem alfabética, 1-20).

insert into public.matches (home_team_id, away_team_id, data_hora, rodada, status) values
  (9,  14, '2026-06-14 16:00:00-03', 13, 'agendado'),  -- Flamengo x Palmeiras
  (18,  6, '2026-06-14 18:30:00-03', 13, 'agendado'),  -- São Paulo x Corinthians
  (11, 12, '2026-06-15 16:00:00-03', 13, 'agendado'),  -- Grêmio x Internacional
  (2,   8, '2026-06-15 18:30:00-03', 13, 'agendado'),  -- Atlético-MG x Cruzeiro
  (4,  10, '2026-06-16 20:00:00-03', 13, 'agendado'),  -- Botafogo x Fluminense
  (19, 17, '2026-06-16 21:30:00-03', 13, 'agendado');  -- Vasco x Santos
