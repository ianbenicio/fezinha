-- Fezinha — Seed 004: Força dos times Série A (rodadas 1-18)
-- Derivado da Tabela Detalhada CBF 2026 via engine/ingestion/cbf_tabela.py.
-- ataque/defesa relativos à média da liga (1.0 = média). Mata o "modo baseline".
-- defesa > 1.0 = time sofre mais que a média (frágil); < 1.0 = defesa sólida.

update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',0.998,'defesa',0.748,'jogos',18,'gols_marcados',24,'gols_sofridos',18) where slug='athletico-pr';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',0.915,'defesa',0.956,'jogos',18,'gols_marcados',22,'gols_sofridos',23) where slug='atletico-mg';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',1.101,'defesa',1.013,'jogos',17,'gols_marcados',25,'gols_sofridos',23) where slug='bahia';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',1.365,'defesa',1.365,'jogos',17,'gols_marcados',31,'gols_sofridos',31) where slug='botafogo';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',1.039,'defesa',0.790,'jogos',18,'gols_marcados',25,'gols_sofridos',19) where slug='bragantino';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',0.795,'defesa',1.450,'jogos',16,'gols_marcados',17,'gols_sofridos',31) where slug='chapecoense';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',0.748,'defesa',0.795,'jogos',16,'gols_marcados',16,'gols_sofridos',17) where slug='corinthians';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',0.998,'defesa',0.998,'jogos',18,'gols_marcados',24,'gols_sofridos',24) where slug='coritiba';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',1.013,'defesa',1.189,'jogos',17,'gols_marcados',23,'gols_sofridos',27) where slug='cruzeiro';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',1.403,'defesa',0.702,'jogos',16,'gols_marcados',30,'gols_sofridos',15) where slug='flamengo';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',1.164,'defesa',0.956,'jogos',18,'gols_marcados',28,'gols_sofridos',23) where slug='fluminense';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',0.832,'defesa',0.956,'jogos',18,'gols_marcados',20,'gols_sofridos',23) where slug='gremio';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',0.836,'defesa',0.969,'jogos',17,'gols_marcados',19,'gols_sofridos',22) where slug='internacional';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',0.792,'defesa',1.057,'jogos',17,'gols_marcados',18,'gols_sofridos',24) where slug='mirassol';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',1.247,'defesa',0.541,'jogos',18,'gols_marcados',30,'gols_sofridos',13) where slug='palmeiras';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',0.873,'defesa',1.206,'jogos',18,'gols_marcados',21,'gols_sofridos',29) where slug='remo';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',1.081,'defesa',1.206,'jogos',18,'gols_marcados',26,'gols_sofridos',29) where slug='santos';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',0.956,'defesa',0.832,'jogos',18,'gols_marcados',23,'gols_sofridos',20) where slug='sao-paulo';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',0.915,'defesa',1.206,'jogos',18,'gols_marcados',22,'gols_sofridos',29) where slug='vasco';
update public.teams set caracteristicas = caracteristicas || jsonb_build_object('ataque',0.924,'defesa',1.101,'jogos',17,'gols_marcados',21,'gols_sofridos',25) where slug='vitoria';
