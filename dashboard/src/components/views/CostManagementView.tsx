"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { DollarSign, TrendingDown, PieChart, Coins } from "lucide-react";
import { fetchCosts } from "@/lib/api";

export function CostManagementView() {
  const { data: costs, isLoading } = useQuery({
    queryKey: ["costs-details"],
    queryFn: fetchCosts,
  });

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-emerald-400" />
            FinOps & AI Token Cost Management
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Real-time tracking of agent execution, LLM token consumption, and cloud infrastructure expenditure.
          </p>
        </div>
        <div className="text-right">
          <span className="text-[10px] text-slate-500 font-mono">Total Cumulative Spend</span>
          <p className="text-2xl font-bold text-emerald-400">
            ${costs ? costs.total_usd.toFixed(2) : "0.00"}
          </p>
        </div>
      </div>

      {costs?.by_category && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {Object.entries(costs.by_category).map(([cat, amount]) => (
            <div key={cat} className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-1">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                {cat.replace("_", " ")}
              </span>
              <p className="text-lg font-bold text-white font-mono">${amount.toFixed(2)}</p>
            </div>
          ))}
        </div>
      )}

      {/* Breakdown list */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
            FinOps Transaction Ledger ({costs?.records?.length || 0})
          </h4>
        </div>
        <div className="divide-y divide-slate-800/60 max-h-80 overflow-y-auto">
          {costs?.records && costs.records.length > 0 ? (
            costs.records.map((r) => (
              <div key={r.id} className="px-5 py-3 flex items-center justify-between text-xs">
                <div>
                  <span className="font-semibold text-white capitalize">{r.category.replace("_", " ")}</span>
                  <span className="text-[11px] text-slate-500 font-mono ml-2">Project: {r.project_id.slice(0, 8)}</span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="font-mono text-emerald-400 font-bold">${r.amount_usd.toFixed(2)}</span>
                  <span className="text-[10px] font-mono text-slate-500">
                    {new Date(r.recorded_at).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-slate-500 text-xs">No cost records logged yet.</div>
          )}
        </div>
      </div>
    </div>
  );
}
