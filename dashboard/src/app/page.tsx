"use client";

import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Sidebar, ModuleKey } from "@/components/Sidebar";
import { Header } from "@/components/Header";
import { fetchProjects, fetchOverviewStats } from "@/lib/api";

// 18 Module Views
import { OverviewView } from "@/components/views/OverviewView";
import { CloudExecutionCenterView } from "@/components/views/CloudExecutionCenterView";
import { ProductionOperationsCenterView } from "@/components/views/ProductionOperationsCenterView";
import { MaintenanceCenterView } from "@/components/views/MaintenanceCenterView";
import { CreateProjectView } from "@/components/views/CreateProjectView";
import { ProjectManagementView } from "@/components/views/ProjectManagementView";
import { AgentManagementView } from "@/components/views/AgentManagementView";
import { ExecutionMonitorView } from "@/components/views/ExecutionMonitorView";
import { TechSelectionView } from "@/components/views/TechSelectionView";
import { ArchitectureView } from "@/components/views/ArchitectureView";
import { TaskManagementView } from "@/components/views/TaskManagementView";
import { GithubView } from "@/components/views/GithubView";
import { ApiIntegrationView } from "@/components/views/ApiIntegrationView";
import { MetaDeveloperCenterView } from "@/components/views/MetaDeveloperCenterView";
import { DatabaseManagementView } from "@/components/views/DatabaseManagementView";
import { SecurityCenterView } from "@/components/views/SecurityCenterView";
import { QACenterView } from "@/components/views/QACenterView";
import { DeploymentCenterView } from "@/components/views/DeploymentCenterView";
import { ApprovalCenterView } from "@/components/views/ApprovalCenterView";
import { CostManagementView } from "@/components/views/CostManagementView";
import { SystemSettingsView } from "@/components/views/SystemSettingsView";

export default function DashboardPage() {
  const [currentModule, setCurrentModule] = useState<ModuleKey>("overview");
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);

  const { data: projects, refetch: refetchProjects } = useQuery({
    queryKey: ["projects-header"],
    queryFn: fetchProjects,
  });

  const { data: stats, refetch: refetchStats } = useQuery({
    queryKey: ["stats-header"],
    queryFn: fetchOverviewStats,
    refetchInterval: 5000,
  });

  // Automatically select first active project if none selected
  useEffect(() => {
    if (projects && projects.length > 0 && !selectedProjectId) {
      setSelectedProjectId(projects[0].id);
    }
  }, [projects, selectedProjectId]);

  const handleProjectCreated = (newId: string) => {
    refetchProjects();
    setSelectedProjectId(newId);
    setCurrentModule("execution_monitor");
  };

  const handleRefresh = () => {
    refetchProjects();
    refetchStats();
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 font-sans">
      {/* Sidebar */}
      <Sidebar
        currentModule={currentModule}
        onSelectModule={setCurrentModule}
        pendingApprovalsCount={stats?.pending_approvals_count || 0}
      />

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <Header
          currentModule={currentModule}
          projects={projects || []}
          selectedProjectId={selectedProjectId}
          onSelectProject={setSelectedProjectId}
          onNavigate={setCurrentModule}
          pendingApprovalsCount={stats?.pending_approvals_count || 0}
          onRefresh={handleRefresh}
        />

        {/* Viewport Content Area */}
        <main className="flex-1 overflow-y-auto p-8 scrollbar-thin scrollbar-thumb-slate-800">
          {currentModule === "overview" && <OverviewView onNavigate={setCurrentModule} />}
          {currentModule === "cloud_execution" && <CloudExecutionCenterView />}
          {currentModule === "operations_center" && (
            <ProductionOperationsCenterView projectId={selectedProjectId} />
          )}
          {currentModule === "create_project" && (
            <CreateProjectView onProjectCreated={handleProjectCreated} />
          )}
          {currentModule === "project_management" && (
            <ProjectManagementView
              onSelectProject={setSelectedProjectId}
              onNavigateToMonitor={() => setCurrentModule("execution_monitor")}
            />
          )}
          {currentModule === "agent_management" && <AgentManagementView />}
          {currentModule === "execution_monitor" && (
            <ExecutionMonitorView
              projectId={selectedProjectId}
              onNavigateToApprovals={() => setCurrentModule("approvals")}
            />
          )}
          {currentModule === "tech_selection" && (
            <TechSelectionView projectId={selectedProjectId} />
          )}
          {currentModule === "architecture" && (
            <ArchitectureView projectId={selectedProjectId} />
          )}
          {currentModule === "task_management" && (
            <TaskManagementView projectId={selectedProjectId} />
          )}
          {currentModule === "github" && <GithubView projectId={selectedProjectId} />}
          {currentModule === "api_integration" && <ApiIntegrationView />}
          {currentModule === "meta_developer" && <MetaDeveloperCenterView />}
          {currentModule === "database" && <DatabaseManagementView />}
          {currentModule === "security" && <SecurityCenterView />}
          {currentModule === "qa" && <QACenterView />}
          {currentModule === "deployment" && <DeploymentCenterView />}
          {currentModule === "maintenance_center" && (
            <MaintenanceCenterView projectId={selectedProjectId} />
          )}
          {currentModule === "approvals" && (
            <ApprovalCenterView
              projectId={selectedProjectId}
              onRefreshProject={handleRefresh}
            />
          )}
          {currentModule === "costs" && <CostManagementView />}
          {currentModule === "settings" && <SystemSettingsView />}
        </main>
      </div>
    </div>
  );
}
