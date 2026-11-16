"use client";

import React from "react";
import {
  LayoutDashboard,
  PlusCircle,
  Cloud,
  FolderKanban,
  Bot,
  Activity,
  Layers,
  Cpu,
  CheckSquare,
  GitBranch,
  Network,
  Share2,
  Database,
  ShieldAlert,
  CheckCircle2,
  Rocket,
  ShieldCheck,
  DollarSign,
  Settings,
  HeartPulse,
} from "lucide-react";

export type ModuleKey =
  | "overview"
  | "create_project"
  | "cloud_execution"
  | "operations_center"
  | "project_management"
  | "agent_management"
  | "execution_monitor"
  | "tech_selection"
  | "architecture"
  | "task_management"
  | "github"
  | "api_integration"
  | "meta_developer"
  | "database"
  | "security"
  | "qa"
  | "deployment"
  | "approvals"
  | "costs"
  | "settings";

interface SidebarProps {
  currentModule: ModuleKey;
  onSelectModule: (module: ModuleKey) => void;
  pendingApprovalsCount?: number;
}

interface SidebarItem {
  key: ModuleKey;
  label: string;
  icon: any;
  badge?: string;
  badgeAlert?: boolean;
}

interface SidebarSection {
  title: string;
  items: SidebarItem[];
}

export function Sidebar({ currentModule, onSelectModule, pendingApprovalsCount = 0 }: SidebarProps) {
  const sections: SidebarSection[] = [
    {
      title: "Core Operations",
      items: [
        { key: "overview" as ModuleKey, label: "Overview", icon: LayoutDashboard },
        { key: "create_project" as ModuleKey, label: "Create Project", icon: PlusCircle },
        { key: "operations_center" as ModuleKey, label: "Operations & Self-Healing", icon: HeartPulse, badge: "AIOps" },
        { key: "project_management" as ModuleKey, label: "Projects", icon: FolderKanban },
        { key: "execution_monitor" as ModuleKey, label: "Execution Monitor", icon: Activity },
        { key: "cloud_execution" as ModuleKey, label: "Cloud Execution Center", icon: Cloud, badge: "Fargate" },
      ],
    },
    {
      title: "Architecture & Agents",
      items: [
        { key: "agent_management" as ModuleKey, label: "Specialist Agents", icon: Bot, badge: "97" },
        { key: "tech_selection" as ModuleKey, label: "Technology Selection", icon: Layers },
        { key: "architecture" as ModuleKey, label: "Architecture Viewer", icon: Cpu },
        { key: "task_management" as ModuleKey, label: "Task Workflows", icon: CheckSquare },
      ],
    },
    {
      title: "Integrations & Ecosystem",
      items: [
        { key: "github" as ModuleKey, label: "GitHub Repositories", icon: GitBranch },
        { key: "api_integration" as ModuleKey, label: "Third-Party APIs", icon: Network },
        { key: "meta_developer" as ModuleKey, label: "Meta Developer Center", icon: Share2 },
        { key: "database" as ModuleKey, label: "Database Management", icon: Database },
      ],
    },
    {
      title: "Governance & Quality",
      items: [
        { key: "security" as ModuleKey, label: "Security Center", icon: ShieldAlert },
        { key: "qa" as ModuleKey, label: "QA & Testing", icon: CheckCircle2 },
        { key: "deployment" as ModuleKey, label: "Deployment Center", icon: Rocket },
        {
          key: "approvals" as ModuleKey,
          label: "Approval Center",
          icon: ShieldCheck,
          badge: pendingApprovalsCount > 0 ? `${pendingApprovalsCount}` : undefined,
          badgeAlert: pendingApprovalsCount > 0,
        },
      ],
    },
    {
      title: "Administration",
      items: [
        { key: "costs" as ModuleKey, label: "Cost & FinOps", icon: DollarSign },
        { key: "settings" as ModuleKey, label: "System Settings", icon: Settings },
      ],
    },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 border-r border-slate-800 flex flex-col flex-shrink-0 h-screen select-none">
      {/* Brand */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800 gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center text-white font-bold shadow-lg shadow-indigo-500/20">
          AF
        </div>
        <div>
          <h1 className="text-sm font-bold text-white tracking-wide">AI SOFTWARE FACTORY</h1>
          <p className="text-[11px] text-cyan-400 font-medium">Autonomous Enterprise v1.0</p>
        </div>
      </div>

      {/* Navigation Groups */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6 scrollbar-thin scrollbar-thumb-slate-800">
        {sections.map((sec, idx) => (
          <div key={idx} className="space-y-1">
            <h2 className="px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              {sec.title}
            </h2>
            <div className="space-y-0.5 mt-1">
              {sec.items.map((item) => {
                const Icon = item.icon;
                const isActive = currentModule === item.key;
                return (
                  <button
                    key={item.key}
                    onClick={() => onSelectModule(item.key)}
                    className={`w-full flex items-center justify-between px-3 py-2 text-xs font-medium rounded-lg transition-colors ${
                      isActive
                        ? "bg-indigo-600 text-white font-semibold shadow-sm"
                        : "text-slate-300 hover:bg-slate-800/80 hover:text-white"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className={`w-4 h-4 ${isActive ? "text-white" : "text-slate-400"}`} />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span
                        className={`px-1.5 py-0.5 text-[10px] font-bold rounded-full ${
                          item.badgeAlert
                            ? "bg-amber-500 text-slate-950 animate-pulse"
                            : isActive
                            ? "bg-indigo-700 text-white"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Operator Status */}
      <div className="p-3 border-t border-slate-800 text-xs flex items-center justify-between bg-slate-950/60">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[11px] font-medium text-slate-300">FastAPI Orchestrator</span>
        </div>
        <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-1.5 py-0.5 rounded">
          Connected
        </span>
      </div>
    </aside>
  );
}
