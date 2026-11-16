"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Cloud,
  Server,
  Play,
  Pause,
  RotateCcw,
  XCircle,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Shield,
  Activity,
  DollarSign,
  Cpu,
  Layers,
  ExternalLink,
  RefreshCw,
  GitPullRequest,
  Archive,
  ArrowRight,
} from "lucide-react";
import {
  fetchCloudStatus,
  fetchCloudJobs,
  fetchCloudWorkers,
  submitCloudJob,
  pauseCloudJob,
  resumeCloudJob,
  cancelCloudJob,
  retryCloudJob,
  triggerCloudRecovery,
  fetchProjects,
} from "@/lib/api";

export function CloudExecutionCenterView() {
  const queryClient = useQueryClient();
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [targetStage, setTargetStage] = useState<number>(23);
  const [priority, setPriority] = useState<number>(5);
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  const { data: cloudStatus, isLoading: statusLoading } = useQuery({
    queryKey: ["cloud-status"],
    queryFn: fetchCloudStatus,
    refetchInterval: 4000,
  });

  const { data: jobs, isLoading: jobsLoading } = useQuery({
    queryKey: ["cloud-jobs"],
    queryFn: () => fetchCloudJobs(),
    refetchInterval: 3000,
  });

  const { data: workers, isLoading: workersLoading } = useQuery({
    queryKey: ["cloud-workers"],
    queryFn: fetchCloudWorkers,
    refetchInterval: 4000,
  });

  const { data: projects } = useQuery({
    queryKey: ["projects-list-cloud"],
    queryFn: fetchProjects,
  });

  const submitJobMutation = useMutation({
    mutationFn: (pId: string) => submitCloudJob(pId, targetStage, priority),
    onSuccess: (data) => {
      setFeedbackMsg(`Job ${data.job_id.slice(0, 8)} queued successfully for project ${data.project_id.slice(0, 8)}!`);
      queryClient.invalidateQueries({ queryKey: ["cloud-jobs"] });
      queryClient.invalidateQueries({ queryKey: ["cloud-status"] });
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
  });

  const pauseMutation = useMutation({
    mutationFn: pauseCloudJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cloud-jobs"] });
      queryClient.invalidateQueries({ queryKey: ["cloud-status"] });
    },
  });

  const resumeMutation = useMutation({
    mutationFn: resumeCloudJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cloud-jobs"] });
      queryClient.invalidateQueries({ queryKey: ["cloud-status"] });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: cancelCloudJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cloud-jobs"] });
      queryClient.invalidateQueries({ queryKey: ["cloud-status"] });
    },
  });

  const retryMutation = useMutation({
    mutationFn: retryCloudJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cloud-jobs"] });
      queryClient.invalidateQueries({ queryKey: ["cloud-status"] });
    },
  });

  const recoveryMutation = useMutation({
    mutationFn: triggerCloudRecovery,
    onSuccess: (data) => {
      setFeedbackMsg(`Recovery cycle finished: ${data.recovered_jobs_count} jobs recovered, ${data.unhealthy_workers_count} stale workers pruned.`);
      queryClient.invalidateQueries({ queryKey: ["cloud-jobs"] });
      queryClient.invalidateQueries({ queryKey: ["cloud-workers"] });
      setTimeout(() => setFeedbackMsg(null), 6000);
    },
  });

  const handleDispatch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjectId && projects && projects.length > 0) {
      submitJobMutation.mutate(projects[0].id);
    } else if (selectedProjectId) {
      submitJobMutation.mutate(selectedProjectId);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Cloud className="w-5 h-5 text-sky-400" />
            Cloud Worker & Persistent Execution Center
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Autonomous execution engine running on AWS ECS/Fargate. Projects continue independently when local machines disconnect.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => recoveryMutation.mutate()}
            disabled={recoveryMutation.isPending}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition-colors border border-slate-700"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${recoveryMutation.isPending ? "animate-spin" : ""}`} />
            Run Recovery Scan
          </button>
          <div className="text-right">
            <span className="text-[10px] text-slate-500 font-mono">Persistence Mode</span>
            <p className="text-xs font-bold text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Windows-Disconnected OK
            </p>
          </div>
        </div>
      </div>

      {/* Feedback Banner */}
      {feedbackMsg && (
        <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{feedbackMsg}</span>
          </div>
          <button onClick={() => setFeedbackMsg(null)} className="text-slate-400 hover:text-white text-xs">
            Dismiss
          </button>
        </div>
      )}

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">Cloud Workers (Fargate)</span>
          <p className="text-xs font-mono font-bold text-white mt-1 flex items-center gap-1.5">
            <Server className="w-3.5 h-3.5 text-sky-400" />
            {cloudStatus?.workers?.active || 0} Active / {cloudStatus?.workers?.total_registered || 0} Registered
          </p>
          <span className="text-[10px] text-slate-500 font-mono">
            {cloudStatus?.workers?.busy || 0} Busy • {cloudStatus?.workers?.idle || 0} Idle
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">Persistent Workflow Queue</span>
          <p className="text-xs font-mono font-bold text-cyan-400 mt-1 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5" />
            {cloudStatus?.jobs?.queued || 0} Queued • {cloudStatus?.jobs?.running || 0} Running
          </p>
          <span className="text-[10px] text-slate-500 font-mono">
            {cloudStatus?.jobs?.paused || 0} Paused • {cloudStatus?.jobs?.blocked_on_approval || 0} Awaiting Approval
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">Job Success & DLQ</span>
          <p className="text-xs font-mono font-bold text-emerald-400 mt-1 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            {cloudStatus?.jobs?.completed || 0} Completed
          </p>
          <span className="text-[10px] text-slate-500 font-mono">
            {cloudStatus?.jobs?.failed || 0} Failed • {cloudStatus?.jobs?.dead_letter_queue || 0} in DLQ
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">Fargate FinOps & Budget</span>
          <p className="text-xs font-mono font-bold text-white mt-1 flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
            Cap: ${cloudStatus?.cost_governance?.default_project_budget_usd || 50}.00 / project
          </p>
          <span className="text-[10px] text-slate-500 font-mono">
            Rate: ${cloudStatus?.cost_governance?.vcpu_hourly_rate_usd?.toFixed(4) || "0.0405"}/vCPU-hr
          </span>
        </div>
      </div>

      {/* Dispatch Project Job Form */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-3">
          <Play className="w-4 h-4 text-emerald-400" />
          Dispatch Project to Autonomous Cloud Worker
        </h4>
        <form onSubmit={handleDispatch} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-2">
            <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">Select Project</label>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono focus:outline-none focus:border-sky-500"
            >
              {projects?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.id.slice(0, 8)}) - Stage {p.current_stage || 1}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">Target Stage (1-23)</label>
            <input
              type="number"
              min={1}
              max={23}
              value={targetStage}
              onChange={(e) => setTargetStage(parseInt(e.target.value) || 23)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono focus:outline-none focus:border-sky-500"
            />
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={submitJobMutation.isPending}
              className="w-full py-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center justify-center gap-2 transition-colors shadow-sm"
            >
              <Cloud className="w-3.5 h-3.5" />
              {submitJobMutation.isPending ? "Queueing..." : "Enqueue Cloud Job"}
            </button>
          </div>
        </form>
      </div>

      {/* Real-time Workflow Jobs Queue */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800 flex items-center justify-between">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Layers className="w-4 h-4 text-sky-400" />
            Persistent Workflow Jobs Queue (Durable Execution)
          </h4>
          <span className="text-[10px] text-slate-500 font-mono">Auto-refreshed</span>
        </div>

        {!jobs || jobs.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-500 font-mono">
            No active or queued workflow jobs. Dispatch a project above to initiate autonomous execution.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/50 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="p-3">Job ID</th>
                  <th className="p-3">Project</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Stage</th>
                  <th className="p-3">Assigned Worker</th>
                  <th className="p-3">Retries</th>
                  <th className="p-3 text-right">Controls</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 font-mono text-[11px]">
                {jobs.map((j) => (
                  <tr key={j.id} className="hover:bg-slate-800/20">
                    <td className="p-3 font-semibold text-white">{j.id.slice(0, 8)}</td>
                    <td className="p-3 text-slate-300">{j.project_id.slice(0, 8)}</td>
                    <td className="p-3">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] ${
                          j.status === "completed"
                            ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800/40"
                            : j.status === "running"
                            ? "bg-sky-950/60 text-sky-400 border border-sky-800/40"
                            : j.status === "paused"
                            ? "bg-amber-950/60 text-amber-400 border border-amber-800/40"
                            : j.status === "failed"
                            ? "bg-rose-950/60 text-rose-400 border border-rose-800/40"
                            : "bg-slate-800 text-slate-300"
                        }`}
                      >
                        {j.status}
                      </span>
                    </td>
                    <td className="p-3 text-cyan-400">
                      {j.current_stage} / {j.target_stage}
                    </td>
                    <td className="p-3 text-slate-400">
                      {j.assigned_worker_id ? j.assigned_worker_id.slice(0, 8) : "Awaiting Worker"}
                    </td>
                    <td className="p-3 text-slate-400">{j.retry_count}</td>
                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {j.status === "running" && (
                          <button
                            onClick={() => pauseMutation.mutate(j.id)}
                            title="Pause Job"
                            className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-amber-400"
                          >
                            <Pause className="w-3 h-3" />
                          </button>
                        )}
                        {j.status === "paused" && (
                          <button
                            onClick={() => resumeMutation.mutate(j.id)}
                            title="Resume Job"
                            className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-emerald-400"
                          >
                            <Play className="w-3 h-3" />
                          </button>
                        )}
                        {j.status === "failed" && (
                          <button
                            onClick={() => retryMutation.mutate(j.id)}
                            title="Retry Job"
                            className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-sky-400"
                          >
                            <RotateCcw className="w-3 h-3" />
                          </button>
                        )}
                        {["queued", "running", "paused"].includes(j.status) && (
                          <button
                            onClick={() => cancelMutation.mutate(j.id)}
                            title="Cancel Job"
                            className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-rose-400"
                          >
                            <XCircle className="w-3 h-3" />
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

      {/* Cloud Worker Nodes Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800 flex items-center justify-between">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Server className="w-4 h-4 text-emerald-400" />
            Registered Cloud Execution Workers (ECS Fargate)
          </h4>
          <span className="text-[10px] text-slate-500 font-mono">Cluster: {cloudStatus?.infrastructure?.cluster_name || "ai-factory-cluster"}</span>
        </div>

        {!workers || workers.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-500 font-mono">
            No cloud workers connected. Launch worker container (`docker-compose -f docker/docker-compose.cloud.yml up`) or run `python3 -m factory.cloud_worker.daemon`.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/50 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="p-3">Worker Node</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">vCPU / RAM</th>
                  <th className="p-3">Current Job</th>
                  <th className="p-3">Jobs Completed</th>
                  <th className="p-3">Last Heartbeat</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 font-mono text-[11px]">
                {workers.map((w) => (
                  <tr key={w.id} className="hover:bg-slate-800/20">
                    <td className="p-3 font-semibold text-white">{w.worker_name}</td>
                    <td className="p-3">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] ${
                          w.status === "busy"
                            ? "bg-sky-950/60 text-sky-400 border border-sky-800/40"
                            : w.status === "idle"
                            ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800/40"
                            : "bg-rose-950/60 text-rose-400 border border-rose-800/40"
                        }`}
                      >
                        {w.status}
                      </span>
                    </td>
                    <td className="p-3 text-slate-300">
                      {w.cpu_cores} vCPU • {w.memory_mb} MB
                    </td>
                    <td className="p-3 text-cyan-400">
                      {w.current_job_id ? w.current_job_id.slice(0, 8) : "None"}
                    </td>
                    <td className="p-3 text-slate-300">{w.total_jobs_completed}</td>
                    <td className="p-3 text-slate-500 text-[10px]">
                      {w.last_heartbeat ? new Date(w.last_heartbeat).toLocaleTimeString() : "N/A"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Cloud Infrastructure & Governance Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-2">
          <h4 className="text-xs font-bold text-white uppercase flex items-center gap-2">
            <Archive className="w-4 h-4 text-amber-400" />
            S3 Artifact Storage & Builds
          </h4>
          <p className="text-[11px] text-slate-400">
            Build archives (.tar.gz) are packaged after each stage and uploaded to AWS S3:
          </p>
          <div className="bg-slate-950 p-2.5 rounded border border-slate-800/80 font-mono text-[11px] text-slate-300">
            Bucket: {cloudStatus?.infrastructure?.s3_bucket || "ai-software-factory-artifacts"}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-2">
          <h4 className="text-xs font-bold text-white uppercase flex items-center gap-2">
            <GitPullRequest className="w-4 h-4 text-purple-400" />
            GitHub Branch & PR Isolation Policy
          </h4>
          <p className="text-[11px] text-slate-400">
            Cloud workers commit to isolated feature branches (`feature/project-build`) and open Pull Requests. Direct push to `main` is disallowed.
          </p>
          <div className="bg-slate-950 p-2.5 rounded border border-slate-800/80 font-mono text-[11px] text-emerald-400">
            Main branch protection: ACTIVE
          </div>
        </div>
      </div>
    </div>
  );
}
