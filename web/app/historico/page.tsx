"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

type Consulta = {
  id: number;
  match_id: number;
  complexidade: string;
  custo_creditos: number;
  mercados: string[];
  status: string;
  created_at: string;
};

export default function HistoricoPage() {
  const [consultas, setConsultas] = useState<Consulta[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<{ consultas: Consulta[] }>("/queries")
      .then((r) => setConsultas(r.consultas))
      .catch(() => setConsultas([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-white/60">Carregando...</p>;

  return (
    <div>
      <h1 className="mb-4 text-xl font-bold">Histórico de consultas</h1>
      {consultas.length === 0 ? (
        <p className="text-white/60">Nenhuma consulta ainda.</p>
      ) : (
        <table className="w-full text-sm">
          <thead className="text-left text-white/50">
            <tr>
              <th className="py-2">Data</th>
              <th>Partida</th>
              <th>Plano</th>
              <th>Custo</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {consultas.map((c) => (
              <tr key={c.id} className="border-t border-white/10">
                <td className="py-2">{new Date(c.created_at).toLocaleString("pt-BR")}</td>
                <td>#{c.match_id}</td>
                <td>{c.complexidade}</td>
                <td>{c.custo_creditos} cr</td>
                <td>
                  <span className={c.status === "concluida" ? "text-fz-green" : "text-white/50"}>
                    {c.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
