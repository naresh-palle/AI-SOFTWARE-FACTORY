"use client";

import React from "react";
import {
  Bell,
  Search,
  Plus,
  RefreshCw,
  Activity,
  FolderOpen,
  ChevronDown,
} from "lucide-react";
import { ModuleKey } from "./Sidebar";

interface HeaderProps {
  currentModule: ModuleKey;
  projects: Array<{ id: string; name: string }>;
  selectedProjectId: string | null;
  onSelectProject: (id: string) => void;
  onNavigate: (module: ModuleKey) => void;
  pendingApprovalsCount?: number;
  onRefresh?: () => void;
}

const moduleTitles: Record<ModuleKey, { title: string; subtitle: string }> = {
  overview: { title: "Operations Overview", subtitle: "Real-time AI Software Factory metrics & autonomous workflows" },
  create_project: { title: "Create Software Project", subtitle: "Enter natural language software requirements to activate agents" },
  cloud_execution: { title: "Cloud Execution Center", subtitle: "Autonomous execution engine running on AWS ECS/Fargate with persistent recovery" },
  project_management: { title: "Project Portfolio", subtitle: "Manage active and completed multi-agent projects" },
  agent_management: { title: "Specialist Agent Registry", subtitle: "97 specialized autonomous engineering roles across 10 disciplines" },
  execution_monitor: { title: "Agent Execution Monitor", subtitle: "Live pipeline tracker with verifiable deliverables across 23 stages" },
  tech_selection: { title: "Dynamic Technology Selection", subtitle: "Automated stack architecture and technology decisions per project" },
  architecture: { title: "Architecture Viewer", subtitle: "System topology, microservices, and communication diagrams" },
  task_management: { title: "Task Dependency Graph", subtitle: "Granular work breakdown structure and DAG execution" },
  github: { title: "GitHub Version Control", subtitle: "Automated repository creation, branches, and CI/CD pipelines" },
  api_integration: { title: "Third-Party API Integrations", subtitle: "Enterprise payment gateways, notification APIs, and service connectors" },
  meta_developer: { title: "Meta Developer Center", subtitle: "Facebook Graph API, Instagram API, WhatsApp Business Platform" },
  database: { title: "Database Architecture & Management", subtitle: "PostgreSQL, MongoDB, and Redis caching infrastructure" },
  security: { title: "Enterprise Security Center", subtitle: "SAST scans, secrets encryption, vulnerability mitigation, and audit trails" },
  qa: { title: "QA & Verification Center", subtitle: "Automated Pytest, API testing, Playwright UI tests, and quality gates" },
  deployment: { title: "Deployment Center", subtitle: "Kubernetes, Docker, AWS infrastructure, and ArgoCD pipelines" },
  approvals: { title: "Human Governance & Approvals", subtitle: "Mandatory human sign-off gates for production and sensitive operations" },
  costs: { title: "Cost & FinOps Management", subtitle: "AI token consumption, compute costs, and cloud infrastructure budgets" },
  settings: { title: "System Configuration", subtitle: "Factory engine settings, LLM provider routing, and security keys" },
};

export function Header({
  currentModule,
  projects,
  selectedProjectId,
  onSelectProject,
  onNavigate,
  pendingApprovalsCount = 0,
  onRefresh,
}: HeaderProps) {
  const currentInfo = moduleTitles[currentModule] || { title: "Dashboard", subtitle: "" };

  return (
    <header className="h-16 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-8 flex-shrink-0">
      {/* Title & Subtitle */}
      <div>
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          {currentInfo.title}
        </h2>
        <p className="text-[11px] text-slate-400">{currentInfo.subtitle}</p>
      </div>

      {/* Actions & Global Controls */}
      <div className="flex items-center gap-3">
        {/* Project Selector */}
        {projects.length > 0 && (
          <div className="flex items-center gap-2 bg-slate-800/80 border border-slate-700/80 px-3 py-1.5 rounded-lg text-xs">
            <FolderOpen className="w-3.5 h-3.5 text-indigo-400" />
            <select
              value={selectedProjectId || ""}
              onChange={(e) => onSelectProject(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none text-xs font-medium cursor-pointer"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id} className="bg-slate-900 text-slate-200">
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Refresh button */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            title="Refresh live data"
            className="p-1.5 text-slate-400 hover:text-white bg-slate-800/60 hover:bg-slate-800 rounded-lg transition-colors border border-slate-700/50"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        )}

        {/* Approvals Notification Button */}
        <button
          onClick={() => onNavigate("approvals")}
          className={`relative p-1.5 rounded-lg border transition-colors ${
            pendingApprovalsCount > 0
              ? "bg-amber-500/10 border-amber-500/30 text-amber-400 hover:bg-amber-500/20"
              : "bg-slate-800/60 border-slate-700/50 text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
          title={`${pendingApprovalsCount} pending approvals`}
        >
          <Bell className="w-4 h-4" />
          {pendingApprovalsCount > 0 && (
            <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-amber-500 text-slate-950 font-bold text-[9px] flex items-center justify-center animate-bounce">
              {pendingApprovalsCount}
            </span>
          )}
        </button>

        {/* Quick New Project Button */}
        <button
          onClick={() => onNavigate("create_project")}
          className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium px-3 py-1.5 rounded-lg transition-colors shadow-sm shadow-indigo-600/30"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Project</span>
        </button>
      </div>
    </header>
  );
}
