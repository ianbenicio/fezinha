"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { apiGet } from "@/lib/api";
import type { TeamDetail } from "@/lib/types";
import { mockTeamDetail } from "@/lib/mock";
import { Loading, Banner, ErrorState } from "@/components/states";
import { TeamView } from "@/components/TeamView";

export default function TimeDetailPage({ params }: { params: Promise<{ teamId: string }> }) {
  const { teamId } = use(params);
  const router = useRouter();
  const [detail, setDetail] = useState<TeamDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [mockUsado, setMockUsado] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        router.replace("/login");
        return;
      }
      apiGet<{ time: TeamDetail }>(`/catalog/teams/${teamId}`)
        .then((r) => {
          if (!r?.time?.resumo) throw new Error("shape inesperado de /catalog/teams/{id}");
          setDetail(r.time);
        })
        .catch(() => {
          setDetail(mockTeamDetail);
          setMockUsado(true);
        })
        .finally(() => setLoading(false));
    });
  }, [teamId, router]);

  if (loading) return <Loading label="Carregando time..." />;
  if (!detail) return <ErrorState mensagem="Time não encontrado." onRetry={() => location.reload()} />;

  return (
    <div className="space-y-4">
      {mockUsado && (
        <Banner tone="warn" titulo="Dados de exemplo">
          Endpoint <code>/catalog/teams/{teamId}</code> pendente (Codex). Mostrando mock.
        </Banner>
      )}
      <TeamView detail={detail} />
    </div>
  );
}
