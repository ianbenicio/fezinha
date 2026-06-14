import { createClient } from "@supabase/supabase-js";

// Fallback evita quebrar o prerender do build se a env faltar. Em produção
// (Vercel) as NEXT_PUBLIC_* reais são embutidas no bundle em build-time.
const url = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://placeholder.supabase.co";
const key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || "placeholder-anon-key";

// Client de browser. A publishable key é pública por design (RLS protege os dados).
export const supabase = createClient(url, key, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
  },
});
