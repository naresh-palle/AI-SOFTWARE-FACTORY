"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CheckSquare, CheckCircle2, Clock, FileCode, Search } from "lucide-react";
import { fetchProjectTasks } from "@/lib/api";

export function TaskManagementView({ projectId }: { projectId: string | null }) {
  const [search, setSearch] = useState("");

  const { data: tasks, isLoading } = useQuery({
    queryKey: ["project-tasks", projectId],
    queryFn: () => (projectId ? fetchProjectTasks(projectId) : []),
    enabled: !!projectId,
  });

  if (!projectId) {
    return <div className="text-center py-12 text-slate-500 text-xs">Please select a project.</div>;
  }

  const filtered = (tasks || []).filter(
    (t) =>
      t.title.toLowerCase().includes(search.toLowerCase()) ||
      t.agent_name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tasks or agent workers..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
        <span className="text-xs font-mono text-slate-400">Total Tasks: {tasks?.length || 0}</span>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 font-semibold">Stage</th>
              <th className="py-3 px-4 font-semibold">Task Title</th>
              <th className="py-3 px-4 font-semibold">Agent Role</th>
              <th className="py-3 px-4 font-semibold">Status</th>
              <th className="py-3 px-4 font-semibold">Verifiable Evidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-500">
                  Loading tasks...
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-500">
                  No tasks recorded for this project yet.
                </td>
              </tr>
            ) : (
              filtered.map((t) => (
                <tr key={t.id} className="hover:bg-slate-800/30">
                  <td className="py-3 px-4 font-mono text-indigo-400 font-bold">Stage {t.stage}</td>
                  <td className="py-3 px-4 font-semibold text-white">{t.title}</td>
                  <td className="py-3 px-4 text-cyan-300 font-mono text-[11px]">{t.agent_name}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold capitalize ${
                        t.status === "completed"
                          ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800/40"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {t.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-[10px] text-slate-400 truncate max-w-xs">
                    {t.execution_evidence || "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
