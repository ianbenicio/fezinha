-- Fezinha — Migration 003: Débito atômico de créditos
-- FOR UPDATE trava a linha do saldo, evitando race condition entre
-- consultas simultâneas do mesmo usuário.
-- Só o backend (service_role) chama — revoga dos roles públicos.

create or replace function public.consumir_creditos(
  p_user uuid,
  p_custo integer,
  p_motivo text,
  p_query_id bigint default null
)
returns boolean
language plpgsql
security definer set search_path = public
as $$
declare
  v_saldo integer;
begin
  select saldo into v_saldo
    from public.credit_balance
   where user_id = p_user
   for update;

  if v_saldo is null or v_saldo < p_custo then
    return false;
  end if;

  update public.credit_balance
     set saldo = saldo - p_custo, updated_at = now()
   where user_id = p_user;

  insert into public.credit_transactions (user_id, tipo, valor, motivo, query_id)
    values (p_user, 'gasto', -p_custo, p_motivo, p_query_id);

  return true;
end;
$$;

revoke execute on function public.consumir_creditos(uuid, integer, text, bigint)
  from public, anon, authenticated;
