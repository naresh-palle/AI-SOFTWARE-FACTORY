"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  FolderKanban,
  Bot,
  ShieldCheck,
  DollarSign,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Cpu,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  PieChart,
  Pie,
} from "recharts";
import { fetchOverviewStats, fetchProjects, fetchCosts } from "@/lib/api";

export function OverviewView({ onNavigate }: { onNavigate: (module: any) => void }) {
  const { data: stats, isLoading: statsLoading, refetch } = useQuery({
    queryKey: ["overview-stats"],
    queryFn: fetchOverviewStats,
    refetchInterval: 5000,
  });

  const { data: costs } = useQuery({
    queryKey: ["costs-summary"],
    queryFn: fetchCosts,
  });

  const costChartData = costs
    ? Object.entries(costs.by_category).map(([name, value]) => ({ name, value }))
    : [
        { name: "agent_execution", value: 1.25 },
        { name: "llm_tokens", value: 0.8 },
      ];

  const projectStatusData = [
    { name: "Active", value: stats?.active_projects || 0, color: "#6366f1" },
    { name: "Completed", value: stats?.completed_projects || 0, color: "#10b981" },
    { name: "Failed", value: stats?.failed_projects || 0, color: "#ef4444" },
  ];

  return (
    <div className="space-y-6">
      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Projects */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Projects</span>
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <FolderKanban className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{stats?.total_projects ?? "—"}</span>
            <span className="text-xs text-indigo-400 font-medium">
              {stats?.active_projects ?? 0} active
            </span>
          </div>
        </div>

        {/* Registered Agents */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Specialist Agents</span>
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
              <Bot className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{stats?.total_agents ?? 97}</span>
            <span className="text-xs text-cyan-400 font-medium">10 disciplines</span>
          </div>
        </div>

        {/* Pending Approvals */}
        <div
          onClick={() => onNavigate("approvals")}
          className="bg-slate-900 border border-slate-800 p-5 rounded-xl cursor-pointer hover:border-amber-500/50 transition-colors"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Governance Gates</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-amber-400">
              {stats?.pending_approvals_count ?? 0}
            </span>
            <span className="text-xs text-slate-400">awaiting decision</span>
          </div>
        </div>

        {/* Total Cost */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Factory Spend</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <DollarSign className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">
              ${stats ? stats.total_cost_usd.toFixed(2) : "0.00"}
            </span>
            <span className="text-xs text-emerald-400">FinOps tracked</span>
          </div>
        </div>
      </div>

      {/* Middle Grid: Charts & Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cost Distribution Chart */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl lg:col-span-1">
          <h3 className="text-sm font-semibold text-white mb-4">Cost by Category (USD)</h3>
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={costChartData}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={10} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", fontSize: "11px" }}
                />
                <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Audit Activities */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Live Audit Trail & Execution Stream</h3>
            <span className="text-[11px] font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-800/40 px-2 py-0.5 rounded">
              Immutable Trail
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2 px-3 font-medium">Timestamp</th>
                  <th className="py-2 px-3 font-medium">Actor</th>
                  <th className="py-2 px-3 font-medium">Action</th>
                  <th className="py-2 px-3 font-medium">Project ID</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {stats?.recent_activities && stats.recent_activities.length > 0 ? (
                  stats.recent_activities.slice(0, 5).map((act) => (
                    <tr key={act.id} className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 font-mono text-[11px] text-slate-400">
                        {new Date(act.created_at).toLocaleTimeString()}
                      </td>
                      <td className="py-2 px-3 font-semibold text-indigo-300">{act.actor}</td>
                      <td className="py-2 px-3">
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[11px] text-emerald-400 font-mono">
                          {act.action}
                        </span>
                      </td>
                      <td className="py-2 px-3 font-mono text-[11px] text-slate-400">
                        {act.project_id ? act.project_id.slice(0, 8) : "System"}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="py-4 text-center text-slate-500">
                      No recent activities logged yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
