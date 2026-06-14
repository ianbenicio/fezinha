"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { apiGet } from "@/lib/api";

type Noticia = {
  titulo: string; url: string; fonte: string;
  liga: string | null; imagem_url: string | null; publicado_em: string | null;
};

const LIGA_NOME: Record<string, string> = {
  brasileirao_serie_a: "Série A", brasileirao_serie_b: "Série B",
};

export default function NoticiasPage() {
  const router = useRouter();
  const [news, setNews] = useState<Noticia[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtro, setFiltro] = useState<string>("todas");

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) { router.replace("/login"); return; }
      apiGet<{ noticias: Noticia[] }>("/catalog/news?limit=50")
        .then((r) => setNews(r.noticias))
        .catch(() => setNews([]))
        .finally(() => setLoading(false));
    });
  }, [router]);

  if (loading) return <p className="text-white/60">Carregando notícias...</p>;

  const visiveis = filtro === "todas" ? news : news.filter((n) => n.liga === filtro);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">Notícias</h1>
        <select value={filtro} onChange={(e) => setFiltro(e.target.value)}
          className="rounded bg-fz-card px-3 py-1 text-sm outline-none">
          <option value="todas">Todas</option>
          <option value="brasileirao_serie_a">Série A</option>
          <option value="brasileirao_serie_b">Série B</option>
        </select>
      </div>

      {visiveis.length === 0 ? (
        <p className="text-white/50">Sem notícias.</p>
      ) : (
        <ul className="space-y-2">
          {visiveis.map((n) => (
            <li key={n.url}>
              <a href={n.url} target="_blank" rel="noopener noreferrer"
                className="block rounded bg-fz-card px-4 py-3 transition hover:border-fz-green border border-transparent">
                <div className="font-medium">{n.titulo}</div>
                <div className="mt-1 text-xs text-white/40">
                  {n.liga ? `${LIGA_NOME[n.liga] ?? n.liga} · ` : ""}{n.fonte}
                  {n.publicado_em ? ` · ${new Date(n.publicado_em).toLocaleDateString("pt-BR")}` : ""}
                  {" "}↗
                </div>
              </a>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-4 text-xs text-white/30">Fonte: ge.globo — links abrem na fonte original.</p>
    </div>
  );
}
