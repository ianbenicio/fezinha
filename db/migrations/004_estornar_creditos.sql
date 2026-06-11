-- Fezinha — Migration 004: Estorno atômico de créditos
-- Devolve crédito ao usuário e registra como tipo 'estorno'.
-- Usado quando o motor falha após o débito. Só o backend (service_role) chama.

create or replace function public.estornar_creditos(
  p_user uuid,
  p_valor integer,
  p_motivo text,
  p_query_id bigint default null
)
returns void
language plpgsql
security definer set search_path = public
as $$
begin
  update public.credit_balance
     set saldo = saldo + p_valor, updated_at = now()
   where user_id = p_user;

  insert into public.credit_transactions (user_id, tipo, valor, motivo, query_id)
    values (p_user, 'estorno', p_valor, p_motivo, p_query_id);
end;
$$;

revoke execute on function public.estornar_creditos(uuid, integer, text, bigint)
  from public, anon, authenticated;
