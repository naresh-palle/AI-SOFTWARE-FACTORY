"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Cpu, Terminal, Layers } from "lucide-react";
import { fetchProjectArchitecture } from "@/lib/api";

export function ArchitectureView({ projectId }: { projectId: string | null }) {
  const { data: arch, isLoading } = useQuery({
    queryKey: ["project-arch", projectId],
    queryFn: () => (projectId ? fetchProjectArchitecture(projectId) : null),
    enabled: !!projectId,
  });

  if (!projectId) {
    return <div className="text-center py-12 text-slate-500 text-xs">Please select a project.</div>;
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Cpu className="w-5 h-5 text-cyan-400" />
          Component Topology & Communication Flow
        </h3>
        <p className="text-xs text-slate-400 mt-1">
          High-level solution architecture and service boundary topology generated for Project ID {projectId}.
        </p>
      </div>

      {/* Mermaid Architecture Code Box */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <span className="text-xs font-mono text-cyan-400 font-semibold flex items-center gap-1.5">
            <Terminal className="w-4 h-4" /> Mermaid Architecture Definition
          </span>
          <span className="text-[10px] text-slate-500 font-mono">graph TD</span>
        </div>
        <pre className="p-5 font-mono text-xs text-slate-300 overflow-x-auto leading-relaxed bg-slate-950/90">
          {arch?.mermaid_diagram ||
            `graph TD
  ClientWeb[Next.js 14 Web Frontend] --> APIGateway[FastAPI Async Gateway]
  ClientMobile[React Native Mobile] --> APIGateway
  APIGateway --> AuthSvc[Authentication & RBAC]
  APIGateway --> CoreDB[(PostgreSQL Relational DB)]
  APIGateway --> CacheSvc[(Redis Cache & Task Queue)]`}
        </pre>
      </div>
    </div>
  );
}
