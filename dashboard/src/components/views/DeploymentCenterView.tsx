"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Rocket, Server, CheckCircle2, Globe, ExternalLink } from "lucide-react";
import { fetchDeployments } from "@/lib/api";

export function DeploymentCenterView() {
  const { data: deployments, isLoading } = useQuery({
    queryKey: ["deployments-list"],
    queryFn: fetchDeployments,
  });

  const envs = [
    { name: "Development", status: "Active", url: "http://localhost:8000", cluster: "Local WSL2 / Docker" },
    { name: "Staging", status: "Configured", url: "https://staging.factory.local", cluster: "AWS ECS Staging" },
    { name: "Production", status: "Gated", url: "https://app.factory.local", cluster: "AWS EKS Cluster" },
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Rocket className="w-5 h-5 text-indigo-400" />
            Application Deployment Center
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Automated deployment targets across Local, Staging, and Production with ArgoCD progressive delivery.
          </p>
        </div>
        <span className="text-[11px] font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-800/40 px-2.5 py-1 rounded">
          GitOps: ArgoCD
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {envs.map((env, i) => (
          <div key={i} className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white">{env.name}</span>
              <span
                className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                  env.status === "Active"
                    ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                    : env.status === "Gated"
                    ? "bg-amber-950 text-amber-400 border border-amber-800"
                    : "bg-slate-950 text-slate-400"
                }`}
              >
                {env.status}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono truncate">{env.url}</p>
            <div className="pt-2 border-t border-slate-800/80 text-[10px] text-slate-500">
              Cluster: {env.cluster}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
