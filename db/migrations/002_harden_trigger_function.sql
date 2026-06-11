-- Fezinha — Migration 002: Hardening do trigger
-- handle_new_user é trigger-only, mas SECURITY DEFINER ficou exposto via REST
-- (/rest/v1/rpc/handle_new_user) aos roles anon e authenticated.
-- Revoga EXECUTE. O trigger continua funcionando (executa como owner da função).
-- Advisor de segurança: 0028 / 0029.

revoke execute on function public.handle_new_user() from public, anon, authenticated;
