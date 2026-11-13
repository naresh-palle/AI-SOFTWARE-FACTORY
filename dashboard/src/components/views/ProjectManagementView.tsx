"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  FolderKanban,
  Search,
  CheckCircle,
  Clock,
  Play,
  Activity,
  Layers,
  ArrowRight,
} from "lucide-react";
import { fetchProjects } from "@/lib/api";

interface ProjectManagementViewProps {
  onSelectProject: (id: string) => void;
  onNavigateToMonitor: () => void;
}

export function ProjectManagementView({
  onSelectProject,
  onNavigateToMonitor,
}: ProjectManagementViewProps) {
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");

  const { data: projects, isLoading, refetch } = useQuery({
    queryKey: ["projects-list"],
    queryFn: fetchProjects,
  });

  const filteredProjects = (projects || []).filter((p) => {
    const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = filterStatus === "all" || p.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search projects..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          {["all", "in_progress", "completed", "planning"].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
                filterStatus === st
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-950 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              {st.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>

      {/* Projects Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 font-semibold">Project Name</th>
              <th className="py-3 px-4 font-semibold">Platform</th>
              <th className="py-3 px-4 font-semibold">Status</th>
              <th className="py-3 px-4 font-semibold">Stage Progress</th>
              <th className="py-3 px-4 font-semibold">Mode</th>
              <th className="py-3 px-4 font-semibold">Created</th>
              <th className="py-3 px-4 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {isLoading ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500">
                  Loading projects...
                </td>
              </tr>
            ) : filteredProjects.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500">
                  No projects match your filter.
                </td>
              </tr>
            ) : (
              filteredProjects.map((proj) => {
                const stagePercent = Math.round((proj.current_stage / 23) * 100);
                return (
                  <tr key={proj.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-white text-xs">{proj.name}</div>
                      <div className="font-mono text-[10px] text-slate-500">{proj.id}</div>
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-400 capitalize">
                      {proj.platform_target}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                          proj.status === "completed"
                            ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800/40"
                            : proj.status === "in_progress"
                            ? "bg-indigo-950/60 text-indigo-400 border border-indigo-800/40"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {proj.status.replace("_", " ")}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                            style={{ width: `${stagePercent}%` }}
                          />
                        </div>
                        <span className="text-[11px] font-mono text-slate-400">
                          {proj.current_stage}/23
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-400 capitalize">
                      {proj.execution_mode}
                    </td>
                    <td className="py-3 px-4 text-slate-400 text-[11px]">
                      {new Date(proj.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => {
                          onSelectProject(proj.id);
                          onNavigateToMonitor();
                        }}
                        className="inline-flex items-center gap-1.5 bg-slate-800 hover:bg-indigo-600 text-slate-200 hover:text-white px-2.5 py-1 rounded-md text-xs font-medium transition-colors"
                      >
                        <Activity className="w-3.5 h-3.5" />
                        <span>Monitor</span>
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
