"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Layers, Cpu, CheckCircle2, DollarSign } from "lucide-react";
import { fetchProjectArchitecture } from "@/lib/api";

export function TechSelectionView({ projectId }: { projectId: string | null }) {
  const { data: arch, isLoading } = useQuery({
    queryKey: ["project-arch", projectId],
    queryFn: () => (projectId ? fetchProjectArchitecture(projectId) : null),
    enabled: !!projectId,
  });

  if (!projectId) {
    return <div className="text-center py-12 text-slate-500 text-xs">Please select a project.</div>;
  }

  if (isLoading) {
    return <div className="text-center py-12 text-slate-500 text-xs">Loading technology selection...</div>;
  }

  const stackItems = [
    { label: "Frontend Layer", value: arch?.frontend_stack, color: "text-indigo-400" },
    { label: "Backend API Layer", value: arch?.backend_stack, color: "text-cyan-400" },
    { label: "Mobile Application", value: arch?.mobile_stack || "Not Requested", color: "text-purple-400" },
    { label: "Database Layer", value: arch?.database_stack, color: "text-emerald-400" },
    { label: "Cache & Message Broker", value: arch?.cache_stack || "In-Memory", color: "text-amber-400" },
    { label: "Cloud Infrastructure", value: arch?.cloud_stack, color: "text-blue-400" },
    { label: "CI/CD & Automation", value: arch?.ci_cd_stack, color: "text-rose-400" },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            Dynamic Technology Architecture Decision
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Technologies determined dynamically by the Technology Selection Engine based on operational constraints.
          </p>
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-500 font-mono">Monthly Cloud Estimate</span>
          <p className="text-xl font-bold text-emerald-400">
            ${arch?.estimated_cost_usd?.toFixed(2) || "0.00"}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {stackItems.map((item, i) => (
          <div key={i} className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-1.5">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              {item.label}
            </span>
            <p className={`text-sm font-bold ${item.color}`}>{item.value}</p>
          </div>
        ))}
      </div>

      {arch?.selected_agents && (
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-3">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
            Activated Specialist Agents ({arch.selected_agents.length})
          </h4>
          <div className="flex flex-wrap gap-1.5">
            {arch.selected_agents.map((agent: string, i: number) => (
              <span
                key={i}
                className="px-2.5 py-1 rounded-md bg-slate-950 border border-slate-800 text-xs text-slate-300 font-medium"
              >
                {agent}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
