"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import { apiGet } from "@/lib/api";

export function Nav() {
  const [email, setEmail] = useState<string | null>(null);
  const [saldo, setSaldo] = useState<number | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      const user = data.session?.user;
      setEmail(user?.email ?? null);
      if (user) {
        apiGet<{ saldo: number }>("/credits")
          .then((r) => setSaldo(r.saldo))
          .catch(() => setSaldo(null));
      }
    });
    const { data: sub } = supabase.auth.onAuthStateChange((_e, session) => {
      setEmail(session?.user?.email ?? null);
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  async function logout() {
    await supabase.auth.signOut();
    window.location.href = "/login";
  }

  return (
    <nav className="border-b border-white/10 bg-fz-card">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link href="/" className="text-lg font-bold text-fz-green">
          Fezinha
        </Link>
        <div className="flex items-center gap-4 text-sm">
          {email ? (
            <>
              <Link href="/calendario" className="hover:text-fz-green">Calendário</Link>
              <Link href="/historico" className="hover:text-fz-green">Histórico</Link>
              {saldo !== null && (
                <span className="rounded bg-fz-green/20 px-2 py-1 text-fz-green">
                  {saldo} créditos
                </span>
              )}
              <span className="text-white/60">{email}</span>
              <button onClick={logout} className="hover:text-fz-green">Sair</button>
            </>
          ) : (
            <Link href="/login" className="hover:text-fz-green">Entrar</Link>
          )}
        </div>
      </div>
    </nav>
  );
}
