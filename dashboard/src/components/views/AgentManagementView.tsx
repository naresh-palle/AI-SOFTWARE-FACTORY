"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Bot,
  Search,
  Filter,
  CheckCircle2,
  Cpu,
  Shield,
  Layers,
  Code2,
  Wrench,
} from "lucide-react";
import { fetchAgents } from "@/lib/api";

const CATEGORIES = [
  "All Categories",
  "Product and Planning",
  "UI/UX and Frontend",
  "Backend and Mobile",
  "Database",
  "External API Integration",
  "Authentication",
  "Security",
  "DevOps and Cloud",
  "Testing",
  "Maintenance",
];

export function AgentManagementView() {
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All Categories");

  const { data: agents, isLoading } = useQuery({
    queryKey: ["agents-catalog"],
    queryFn: fetchAgents,
  });

  const filteredAgents = (agents || []).filter((agent) => {
    const matchesSearch =
      agent.role_title.toLowerCase().includes(search.toLowerCase()) ||
      agent.description.toLowerCase().includes(search.toLowerCase()) ||
      agent.capabilities.some((c) => c.toLowerCase().includes(search.toLowerCase()));

    const matchesCategory =
      selectedCategory === "All Categories" ||
      agent.category.toLowerCase().includes(selectedCategory.toLowerCase());

    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-6">
      {/* Top Header & Search */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search 97 agents or capabilities..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        {/* Category Dropdown */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Agents Count Banner */}
      <div className="flex items-center justify-between px-1">
        <span className="text-xs font-semibold text-slate-400">
          Showing <span className="text-indigo-400 font-bold">{filteredAgents.length}</span> of 97 Specialist Agents
        </span>
        <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-2 py-0.5 rounded">
          Registered & Ready
        </span>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? (
          <div className="col-span-3 py-12 text-center text-slate-500 text-xs">
            Loading specialist agent catalog...
          </div>
        ) : filteredAgents.length === 0 ? (
          <div className="col-span-3 py-12 text-center text-slate-500 text-xs">
            No agents found matching &quot;{search}&quot;.
          </div>
        ) : (
          filteredAgents.map((ag) => (
            <div
              key={ag.role_number}
              className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex flex-col justify-between hover:border-slate-700 transition-colors space-y-3"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-bold font-mono flex items-center justify-center">
                      #{ag.role_number}
                    </span>
                    <h4 className="text-xs font-bold text-white leading-tight">
                      {ag.role_title}
                    </h4>
                  </div>
                  <span className="px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-[10px] font-medium text-slate-400">
                    {ag.category}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-2 line-clamp-2 leading-relaxed">
                  {ag.description}
                </p>
              </div>

              {/* Capabilities Pills */}
              <div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {ag.capabilities.map((cap, i) => (
                    <span
                      key={i}
                      className="px-1.5 py-0.5 rounded bg-slate-950 text-[10px] text-cyan-400 border border-slate-800 font-mono"
                    >
                      {cap}
                    </span>
                  ))}
                </div>
                <div className="flex items-center justify-between pt-3 mt-3 border-t border-slate-800/80 text-[10px] text-slate-500 font-mono">
                  <span>Model: Default (Mock/Ollama)</span>
                  <span className="text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Ready
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
