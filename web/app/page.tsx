"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { apiGet } from "@/lib/api";
import type { Match, Noticia } from "@/lib/types";
import { DashboardView } from "@/components/DashboardView";

export default function Dashboard() {
  const router = useRouter();
  const [matches, setMatches] = useState<Match[]>([]);
  const [news, setNews] = useState<Noticia[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        router.replace("/login");
        return;
      }
      Promise.all([
        apiGet<{ partidas: Match[] }>("/catalog/matches?status=agendado").catch(() => ({ partidas: [] })),
        apiGet<{ noticias: Noticia[] }>("/catalog/news?limit=5").catch(() => ({ noticias: [] })),
      ])
        .then(([m, n]) => {
          setMatches(m.partidas);
          setNews(n.noticias);
        })
        .finally(() => setLoading(false));
    });
  }, [router]);

  return <DashboardView matches={matches} news={news} loading={loading} />;
}
