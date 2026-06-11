"use client";

import { useState } from "react";
import { supabase } from "@/lib/supabase";

export default function LoginPage() {
  const [modo, setModo] = useState<"login" | "cadastro">("login");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [nome, setNome] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setLoading(true);
    try {
      if (modo === "login") {
        const { error } = await supabase.auth.signInWithPassword({ email, password: senha });
        if (error) throw error;
      } else {
        const { error } = await supabase.auth.signUp({
          email,
          password: senha,
          options: { data: { nome } },
        });
        if (error) throw error;
      }
      window.location.href = "/";
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Falha na autenticação");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm pt-10">
      <h1 className="mb-6 text-2xl font-bold">
        {modo === "login" ? "Entrar" : "Criar conta"}
      </h1>
      <form onSubmit={submit} className="space-y-3">
        {modo === "cadastro" && (
          <input
            className="w-full rounded bg-fz-card px-3 py-2 outline-none"
            placeholder="Nome" value={nome} onChange={(e) => setNome(e.target.value)}
          />
        )}
        <input
          className="w-full rounded bg-fz-card px-3 py-2 outline-none"
          type="email" placeholder="E-mail" value={email}
          onChange={(e) => setEmail(e.target.value)} required
        />
        <input
          className="w-full rounded bg-fz-card px-3 py-2 outline-none"
          type="password" placeholder="Senha" value={senha}
          onChange={(e) => setSenha(e.target.value)} required
        />
        {erro && <p className="text-sm text-red-400">{erro}</p>}
        <button
          disabled={loading}
          className="w-full rounded bg-fz-green py-2 font-semibold text-black disabled:opacity-50"
        >
          {loading ? "..." : modo === "login" ? "Entrar" : "Cadastrar"}
        </button>
      </form>
      <button
        onClick={() => setModo(modo === "login" ? "cadastro" : "login")}
        className="mt-4 text-sm text-white/60 hover:text-fz-green"
      >
        {modo === "login" ? "Não tem conta? Cadastre-se" : "Já tem conta? Entrar"}
      </button>
    </div>
  );
}
