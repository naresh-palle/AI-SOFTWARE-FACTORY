"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Settings, CheckCircle2, Shield, Cpu, Terminal, Key } from "lucide-react";
import { fetchSystemSettings, fetchHealth } from "@/lib/api";

export function SystemSettingsView() {
  const { data: settings } = useQuery({
    queryKey: ["sys-settings"],
    queryFn: fetchSystemSettings,
  });

  const { data: health } = useQuery({
    queryKey: ["sys-health"],
    queryFn: fetchHealth,
  });

  const configRows = [
    { label: "Application Name", value: settings?.app_name || "Autonomous AI Software Development Factory" },
    { label: "Environment Mode", value: settings?.environment || "development" },
    { label: "Default Execution Mode", value: settings?.default_execution_mode || "autonomous" },
    { label: "Active LLM Provider", value: settings?.default_llm_provider || "mock" },
    { label: "Local Ollama Endpoint", value: settings?.ollama_base_url || "http://172.18.0.2:11434" },
    { label: "Ollama Model", value: settings?.ollama_model || "llama3:latest" },
    { label: "GitHub Operator Account", value: settings?.github_username || "naresh-palle" },
    { label: "GitHub Token Configured", value: settings?.has_github_token ? "Yes" : "Optional (Local Git active)" },
    { label: "Meta App Configured", value: settings?.has_meta_app ? "Yes" : "Developer Mode" },
    { label: "Fernet AES-256 Secrets Key", value: settings?.encryption_configured ? "Verified Active" : "Default" },
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Settings className="w-5 h-5 text-indigo-400" />
            System Configuration & Runtime Settings
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Global factory parameters, LLM model routing, and secrets configuration.
          </p>
        </div>
        <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-2.5 py-1 rounded">
          Status: {health?.status || "Healthy"}
        </span>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
            Runtime Engine Configuration
          </h4>
        </div>
        <div className="divide-y divide-slate-800/60">
          {configRows.map((row, idx) => (
            <div key={idx} className="px-5 py-3 flex items-center justify-between text-xs">
              <span className="font-medium text-slate-400">{row.label}</span>
              <span className="font-mono font-bold text-white">{row.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
