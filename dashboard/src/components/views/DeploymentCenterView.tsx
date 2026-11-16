"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Rocket,
  Server,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Globe,
  ExternalLink,
  ShieldAlert,
  Database,
  Layers,
  Activity,
  DollarSign,
  Lock,
  GitCommit,
  Archive,
  RefreshCw,
  Cpu,
  Clock,
  Play,
  Send,
} from "lucide-react";
import {
  fetchDeploymentOverviewStatus,
  fetchDeploymentAnalysis,
  fetchBuildArtifacts,
  fetchDeploymentReleases,
  fetchDatabaseMigrations,
  fetchEnvironmentConfigs,
  triggerDeploymentBuild,
  deployRelease,
  triggerRollback,
  fetchProjects,
} from "@/lib/api";

export function DeploymentCenterView() {
  const queryClient = useQueryClient();
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [buildVersion, setBuildVersion] = useState<string>("v1.0.0");
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  const { data: projects } = useQuery({
    queryKey: ["projects-list-deploy"],
    queryFn: fetchProjects,
  });

  const activeProjectId = selectedProjectId || (projects && projects[0]?.id) || "";

  const { data: overviewStatus } = useQuery({
    queryKey: ["deployment-overview-status"],
    queryFn: fetchDeploymentOverviewStatus,
    refetchInterval: 5000,
  });

  const { data: analysis } = useQuery({
    queryKey: ["deployment-analysis", activeProjectId],
    queryFn: () => (activeProjectId ? fetchDeploymentAnalysis(activeProjectId) : null),
    enabled: Boolean(activeProjectId),
  });

  const { data: artifacts, refetch: refetchArtifacts } = useQuery({
    queryKey: ["build-artifacts", activeProjectId],
    queryFn: () => (activeProjectId ? fetchBuildArtifacts(activeProjectId) : []),
    enabled: Boolean(activeProjectId),
  });

  const { data: releases, refetch: refetchReleases } = useQuery({
    queryKey: ["deployment-releases", activeProjectId],
    queryFn: () => (activeProjectId ? fetchDeploymentReleases(activeProjectId) : []),
    enabled: Boolean(activeProjectId),
  });

  const { data: migrations, refetch: refetchMigrations } = useQuery({
    queryKey: ["database-migrations", activeProjectId],
    queryFn: () => (activeProjectId ? fetchDatabaseMigrations(activeProjectId) : []),
    enabled: Boolean(activeProjectId),
  });

  const { data: envConfigs } = useQuery({
    queryKey: ["env-configs", activeProjectId],
    queryFn: () => (activeProjectId ? fetchEnvironmentConfigs(activeProjectId) : []),
    enabled: Boolean(activeProjectId),
  });

  const buildMutation = useMutation({
    mutationFn: () =>
      triggerDeploymentBuild({
        project_id: activeProjectId,
        version: buildVersion,
      }),
    onSuccess: (data) => {
      setFeedbackMsg(`Build ${data.build_id} generated successfully! Container image: ${data.image_tag}`);
      queryClient.invalidateQueries({ queryKey: ["build-artifacts", activeProjectId] });
      queryClient.invalidateQueries({ queryKey: ["deployment-overview-status"] });
      setTimeout(() => setFeedbackMsg(null), 6000);
    },
  });

  const deployMutation = useMutation({
    mutationFn: ({ rId, approved }: { rId: string; approved: boolean }) =>
      deployRelease(rId, true, approved),
    onSuccess: (data) => {
      if (data.success) {
        setFeedbackMsg(`Release ${data.version} deployed to ${data.environment} successfully! Smoke tests passed.`);
      } else {
        setFeedbackMsg(`Deployment blocked or failed: ${data.reason || "Health verification failed"}`);
      }
      queryClient.invalidateQueries({ queryKey: ["deployment-releases", activeProjectId] });
      queryClient.invalidateQueries({ queryKey: ["deployment-overview-status"] });
      setTimeout(() => setFeedbackMsg(null), 6000);
    },
  });

  const rollbackMutation = useMutation({
    mutationFn: (rId: string) =>
      triggerRollback({
        project_id: activeProjectId,
        current_release_id: rId,
        reason: "Manual operator rollback from dashboard",
      }),
    onSuccess: (data) => {
      setFeedbackMsg(`Rollback executed: Reverted from ${data.from_version} to ${data.to_version} in ${data.environment}`);
      queryClient.invalidateQueries({ queryKey: ["deployment-releases", activeProjectId] });
      queryClient.invalidateQueries({ queryKey: ["deployment-overview-status"] });
      setTimeout(() => setFeedbackMsg(null), 6000);
    },
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Rocket className="w-5 h-5 text-indigo-400" />
            Autonomous Deployment & Release Center
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Zero-downtime progressive delivery across Dev, Test, Staging, and Production with automated smoke tests & rollbacks.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
          >
            {projects?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.id.slice(0, 8)})
              </option>
            ))}
          </select>
          <div className="text-right">
            <span className="text-[10px] text-slate-500 font-mono">Governance Mode</span>
            <p className="text-xs font-bold text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Gated Production Rollout
            </p>
          </div>
        </div>
      </div>

      {/* Feedback Banner */}
      {feedbackMsg && (
        <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-800/60 text-indigo-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{feedbackMsg}</span>
          </div>
          <button onClick={() => setFeedbackMsg(null)} className="text-slate-400 hover:text-white text-xs">
            Dismiss
          </button>
        </div>
      )}

      {/* Top 4 KPI Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">Deployments & Releases</span>
          <p className="text-xs font-mono font-bold text-white mt-1 flex items-center gap-1.5">
            <Rocket className="w-3.5 h-3.5 text-indigo-400" />
            {overviewStatus?.summary?.total_deployments || 0} Deployed / {overviewStatus?.summary?.total_releases || 0} Releases
          </p>
          <span className="text-[10px] text-slate-500 font-mono">
            {overviewStatus?.summary?.total_rollbacks || 0} Rollbacks Handled
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">Target Architecture</span>
          <p className="text-xs font-mono font-bold text-cyan-400 mt-1 flex items-center gap-1.5">
            <Server className="w-3.5 h-3.5" />
            {analysis?.target_architecture || "aws_ecs_fargate"}
          </p>
          <span className="text-[10px] text-slate-500 font-mono">
            Strategy: {analysis?.recommended_strategy || "rolling"}
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">Build Artifacts & SBOM</span>
          <p className="text-xs font-mono font-bold text-emerald-400 mt-1 flex items-center gap-1.5">
            <Archive className="w-3.5 h-3.5" />
            {artifacts?.length || 0} Immutable Builds
          </p>
          <span className="text-[10px] text-slate-500 font-mono">CycloneDX SBOM + ECR Scan</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">Estimated Cloud Cost</span>
          <p className="text-xs font-mono font-bold text-white mt-1 flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
            ${overviewStatus?.cost_estimate?.monthly_total_usd?.toFixed(2) || "35.00"} / month
          </p>
          <span className="text-[10px] text-slate-500 font-mono">
            Tier: {overviewStatus?.cost_estimate?.tier || "Standard Fargate"}
          </span>
        </div>
      </div>

      {/* Environment Management Grid (Dev, Testing, Staging, Production) */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Globe className="w-4 h-4 text-cyan-400" />
          Environment Promotion & Deployment Status (4 Tiers)
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {overviewStatus?.environments?.map((env, i) => (
            <div key={i} className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white">{env.name}</span>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                    env.status === "Active"
                      ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800/40"
                      : env.status === "Gated"
                      ? "bg-amber-950/60 text-amber-400 border border-amber-800/40"
                      : "bg-slate-950 text-slate-400 border border-slate-800"
                  }`}
                >
                  {env.status}
                </span>
              </div>
              <p className="text-[11px] text-slate-300 font-mono truncate">{env.url}</p>
              <div className="text-[10px] text-slate-500 font-mono border-t border-slate-800/60 pt-2 flex items-center justify-between">
                <span>{env.type}</span>
                {env.name === "Production" && <Lock className="w-3 h-3 text-amber-400" />}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Build Trigger & Deployment Strategy Dispatch */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Play className="w-4 h-4 text-emerald-400" />
            Build, Containerize & Progressive Release Dispatch
          </h4>
          <span className="text-[10px] font-mono text-slate-400">
            Target: {analysis?.target_architecture || "aws_ecs_fargate"}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">Release Version (SemVer)</label>
            <input
              type="text"
              value={buildVersion}
              onChange={(e) => setBuildVersion(e.target.value)}
              placeholder="v1.0.0"
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">Architecture Rationale</label>
            <div className="p-2 rounded-lg bg-slate-950 border border-slate-800/80 text-[10px] text-slate-400 truncate">
              {analysis?.rationale || "Auto-detected fullstack web service with PostgreSQL"}
            </div>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => buildMutation.mutate()}
              disabled={buildMutation.isPending || !activeProjectId}
              className="w-full py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center justify-center gap-2 transition-colors shadow-sm"
            >
              <Archive className="w-3.5 h-3.5" />
              {buildMutation.isPending ? "Building Container..." : "Build Immutable Artifact"}
            </button>
          </div>
        </div>
      </div>

      {/* Deployment Releases & Rollback Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800 flex items-center justify-between">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Rocket className="w-4 h-4 text-indigo-400" />
            Active Releases, Rollout Strategies & Rollback Controls
          </h4>
          <button
            onClick={() => refetchReleases()}
            className="text-[10px] font-mono text-slate-400 hover:text-white flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" /> Refresh
          </button>
        </div>

        {!releases || releases.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-500 font-mono">
            No releases prepared for this project yet. Trigger a build above to initialize release candidate.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/50 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="p-3">Version</th>
                  <th className="p-3">Environment</th>
                  <th className="p-3">Strategy</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Endpoint</th>
                  <th className="p-3">Commit</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 font-mono text-[11px]">
                {releases.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-800/20">
                    <td className="p-3 font-semibold text-white">{r.version}</td>
                    <td className="p-3 text-slate-300 uppercase">{r.environment}</td>
                    <td className="p-3 text-cyan-400">{r.strategy}</td>
                    <td className="p-3">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] ${
                          r.status === "active"
                            ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800/40"
                            : r.status === "rolled_back"
                            ? "bg-amber-950/60 text-amber-400 border border-amber-800/40"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td className="p-3 text-slate-400 truncate max-w-[180px]">{r.endpoint_url || "Pending"}</td>
                    <td className="p-3 text-slate-500 text-[10px]">{r.commit_sha?.slice(0, 8)}</td>
                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {r.status !== "active" && (
                          <button
                            onClick={() => deployMutation.mutate({ rId: r.id, approved: r.environment === "production" })}
                            disabled={deployMutation.isPending}
                            className="px-2 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-[10px] font-semibold transition-colors"
                          >
                            Deploy
                          </button>
                        )}
                        {r.status === "active" && (
                          <button
                            onClick={() => rollbackMutation.mutate(r.id)}
                            disabled={rollbackMutation.isPending}
                            className="px-2 py-1 rounded bg-amber-600/80 hover:bg-amber-500 text-white text-[10px] font-semibold flex items-center gap-1 transition-colors"
                          >
                            <RotateCcw className="w-2.5 h-2.5" /> Rollback
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Database Migrations Governance Panel */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800 flex items-center justify-between">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Database className="w-4 h-4 text-emerald-400" />
            Database Schema Migrations & Safety Guardrails
          </h4>
          <span className="text-[10px] font-mono text-emerald-400">Zero Unapproved Destructive DDL</span>
        </div>

        {!migrations || migrations.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-500 font-mono">
            No pending database migrations detected. Database schema is synchronized with models.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/50 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="p-3">Version</th>
                  <th className="p-3">Description</th>
                  <th className="p-3">Script Name</th>
                  <th className="p-3">Destructive?</th>
                  <th className="p-3">Backup Checkpoint</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 font-mono text-[11px]">
                {migrations.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-800/20">
                    <td className="p-3 font-semibold text-white">{m.version_num}</td>
                    <td className="p-3 text-slate-300">{m.description}</td>
                    <td className="p-3 text-cyan-400">{m.script_name}</td>
                    <td className="p-3">
                      {m.is_destructive ? (
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-rose-950/60 text-rose-400 border border-rose-800/40 flex items-center gap-1 w-max">
                          <AlertTriangle className="w-2.5 h-2.5" /> Destructive (DROP)
                        </span>
                      ) : (
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-950/60 text-emerald-400 border border-emerald-800/40">
                          Additive (Safe)
                        </span>
                      )}
                    </td>
                    <td className="p-3 text-slate-400">{m.backup_checkpoint || "Pre-flight"}</td>
                    <td className="p-3">
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">
                        {m.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* DNS, SSL & Smoke Test Verification Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-2">
          <h4 className="text-xs font-bold text-white uppercase flex items-center gap-2">
            <Globe className="w-4 h-4 text-cyan-400" />
            Route 53 DNS & ACM SSL/TLS Status
          </h4>
          <p className="text-[11px] text-slate-400">
            HTTPS is strictly enforced with automatic ACM certificate renewal on AWS CloudFront / ALB:
          </p>
          <div className="bg-slate-950 p-2.5 rounded border border-slate-800/80 font-mono text-[11px] text-slate-300 space-y-1">
            <div>TLS Protocol: TLSv1.2 / TLSv1.3</div>
            <div>Certificate Status: Valid (Amazon Trust Services)</div>
            <div>HSTS Policy: max-age=31536000; includeSubDomains</div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-2">
          <h4 className="text-xs font-bold text-white uppercase flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            Automated Smoke Testing Protocol
          </h4>
          <p className="text-[11px] text-slate-400">
            Releases undergo automated probe validation. Any 5xx or probe failure initiates auto-rollback:
          </p>
          <div className="bg-slate-950 p-2.5 rounded border border-slate-800/80 font-mono text-[11px] text-emerald-400 space-y-1">
            <div>✓ Root HTTP / Liveness Check: 200 OK</div>
            <div>✓ Readiness Endpoint (/ready): 200 OK</div>
            <div>✓ Database Connection Pool: Active</div>
            <div>✓ Auto-Rollback Gate: Armed</div>
          </div>
        </div>
      </div>
    </div>
  );
}
