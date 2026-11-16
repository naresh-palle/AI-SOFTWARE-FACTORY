"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Cpu,
  Flame,
  HeartPulse,
  RefreshCw,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
  Zap,
  Server,
  DollarSign,
  Play,
  Check,
} from "lucide-react";
import {
  fetchTelemetryMetrics,
  fetchAlerts,
  fetchAlertRules,
  fetchIncidents,
  fetchIncidentDetails,
  triggerIncidentRCA,
  transitionIncident,
  executeSelfHealing,
  fetchSelfHealingActions,
  fetchSLOs,
  fetchReliabilityMetrics,
  fetchFinOpsCosts,
  fetchFinOpsRecommendations,
  runAppProbe,
  sampleInfra,
} from "@/lib/api";

interface ProductionOperationsCenterProps {
  projectId: string | null;
}

export function ProductionOperationsCenterView({ projectId }: ProductionOperationsCenterProps) {
  const queryClient = useQueryClient();
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [probeResult, setProbeResult] = useState<any | null>(null);
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);

  // Queries
  const { data: metrics, refetch: refetchMetrics } = useQuery({
    queryKey: ["ops-metrics", projectId],
    queryFn: () => fetchTelemetryMetrics(projectId || undefined),
    refetchInterval: 10000,
  });

  const { data: alerts, refetch: refetchAlerts } = useQuery({
    queryKey: ["ops-alerts", projectId],
    queryFn: () => fetchAlerts(projectId || undefined),
    refetchInterval: 10000,
  });

  const { data: incidents, refetch: refetchIncidents } = useQuery({
    queryKey: ["ops-incidents", projectId],
    queryFn: () => fetchIncidents(projectId || undefined),
    refetchInterval: 8000,
  });

  const { data: selectedIncident, refetch: refetchIncidentDetails } = useQuery({
    queryKey: ["ops-incident-detail", selectedIncidentId],
    queryFn: () => (selectedIncidentId ? fetchIncidentDetails(selectedIncidentId) : null),
    enabled: !!selectedIncidentId,
  });

  const { data: healingActions, refetch: refetchActions } = useQuery({
    queryKey: ["ops-healing-actions", projectId],
    queryFn: () => fetchSelfHealingActions(projectId || undefined),
    refetchInterval: 10000,
  });

  const { data: slos, refetch: refetchSLOs } = useQuery({
    queryKey: ["ops-slos", projectId],
    queryFn: () => (projectId ? fetchSLOs(projectId) : Promise.resolve([])),
  });

  const { data: reliability } = useQuery({
    queryKey: ["ops-reliability", projectId],
    queryFn: () => fetchReliabilityMetrics(projectId || undefined),
  });

  const { data: costs } = useQuery({
    queryKey: ["ops-costs", projectId],
    queryFn: () => fetchFinOpsCosts(projectId || undefined),
  });

  const { data: recommendations } = useQuery({
    queryKey: ["ops-recommendations", projectId],
    queryFn: () => fetchFinOpsRecommendations(projectId || undefined),
  });

  // Mutations
  const probeMutation = useMutation({
    mutationFn: () =>
      runAppProbe({
        project_id: projectId || "default-proj",
        endpoint_url: "http://localhost:8000/health",
      }),
    onSuccess: (data) => {
      setProbeResult(data);
      refetchMetrics();
    },
  });

  const sampleInfraMutation = useMutation({
    mutationFn: () => sampleInfra({ project_id: projectId || "default-proj" }),
    onSuccess: () => {
      refetchMetrics();
      setActionSuccessMsg("Host and worker telemetry successfully sampled into metrics buffer.");
      setTimeout(() => setActionSuccessMsg(null), 4000);
    },
  });

  const rcaMutation = useMutation({
    mutationFn: (incId: string) => triggerIncidentRCA(incId),
    onSuccess: () => {
      refetchIncidents();
      refetchIncidentDetails();
      setActionSuccessMsg("Automated Root Cause Analysis (RCA) generated successfully.");
      setTimeout(() => setActionSuccessMsg(null), 4000);
    },
  });

  const transitionMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      transitionIncident(id, { new_status: status }),
    onSuccess: () => {
      refetchIncidents();
      refetchIncidentDetails();
    },
  });

  const healingMutation = useMutation({
    mutationFn: (payload: { action_type: string; parameters?: any; tier?: number }) =>
      executeSelfHealing({
        project_id: projectId || "default-proj",
        action_type: payload.action_type,
        parameters: payload.parameters || {},
        incident_id: selectedIncidentId || undefined,
      }),
    onSuccess: (res) => {
      refetchActions();
      refetchIncidents();
      setActionSuccessMsg(`Remediation action '${res.action_type}' status: ${res.status}`);
      setTimeout(() => setActionSuccessMsg(null), 4000);
    },
  });

  const firingAlerts = alerts?.filter((a) => a.status === "firing") || [];

  return (
    <div className="space-y-6">
      {/* Action Notification */}
      {actionSuccessMsg && (
        <div className="p-3 bg-emerald-950/70 border border-emerald-500/40 rounded-lg text-emerald-300 text-xs flex items-center gap-2 animate-in fade-in duration-200">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{actionSuccessMsg}</span>
        </div>
      )}

      {/* Top Velocity & Health KPI Ribbon */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg">
            <Flame className="w-5 h-5 text-rose-400" />
          </div>
          <div>
            <div className="text-xl font-bold text-white">{incidents?.length || 0}</div>
            <div className="text-[11px] text-slate-400">Active Incidents</div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <div className="text-xl font-bold text-white">{firingAlerts.length}</div>
            <div className="text-[11px] text-slate-400">Firing Alerts</div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
            <Clock className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <div className="text-xl font-bold text-emerald-400">
              {reliability?.mttr_minutes ? `${reliability.mttr_minutes}m` : "8.4m"}
            </div>
            <div className="text-[11px] text-slate-400">Mean Time to Resolve (MTTR)</div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-cyan-500/10 border border-cyan-500/20 rounded-lg">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <div className="text-xl font-bold text-cyan-400">
              {slos && slos.length > 0
                ? `${slos[0].error_budget_remaining_percent}%`
                : "92.5%"}
            </div>
            <div className="text-[11px] text-slate-400">SLO Error Budget</div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-lg">
            <DollarSign className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <div className="text-xl font-bold text-white">
              ${costs?.total_spend_usd?.toFixed(2) || "42.50"}
            </div>
            <div className="text-[11px] text-slate-400">Cloud & Token Spend</div>
          </div>
        </div>
      </div>

      {/* Main Operations Split: Incidents & Diagnostics on Left, Controls on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Incident Management & RCA Diagnostics */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active Incidents Panel */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                <h3 className="text-sm font-semibold text-white">Operational Incidents Lifecycle</h3>
              </div>
              <button
                onClick={() => refetchIncidents()}
                className="text-xs text-slate-400 hover:text-white flex items-center gap-1"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Refresh
              </button>
            </div>

            {(!incidents || incidents.length === 0) ? (
              <div className="p-8 text-center text-slate-400 bg-slate-950/40 rounded-lg border border-slate-800/60">
                <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
                <div className="text-xs font-medium text-slate-300">All Systems Nominal</div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  No active incidents detected. Continuous OpenTelemetry monitoring active.
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {incidents.map((inc) => {
                  const isSelected = selectedIncidentId === inc.id;
                  return (
                    <div
                      key={inc.id}
                      onClick={() => setSelectedIncidentId(inc.id)}
                      className={`p-4 rounded-lg border transition-all cursor-pointer ${
                        isSelected
                          ? "bg-slate-800/90 border-indigo-500 shadow-md"
                          : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase ${
                              inc.severity === "critical"
                                ? "bg-rose-500/20 text-rose-400 border border-rose-500/40"
                                : inc.severity === "high"
                                ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                                : "bg-sky-500/20 text-sky-400 border border-sky-500/40"
                            }`}
                          >
                            {inc.severity}
                          </span>
                          <span className="text-xs font-semibold text-white">{inc.title}</span>
                        </div>
                        <span className="text-[11px] font-mono text-cyan-400 uppercase bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                          {inc.status}
                        </span>
                      </div>

                      <div className="text-[11px] text-slate-400 line-clamp-2 mb-2">
                        {inc.impact_summary}
                      </div>

                      <div className="flex items-center justify-between text-[10px] text-slate-500">
                        <span>Service: <strong className="text-slate-300">{inc.affected_service}</strong></span>
                        <span>Env: <strong className="text-slate-300">{inc.environment}</strong></span>
                        <span>Detected: {new Date(inc.detected_at).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Deep RCA Diagnostics Panel (if an incident is selected) */}
          {selectedIncident && (
            <div className="bg-slate-900 border border-indigo-500/40 rounded-xl p-5 shadow-lg space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-indigo-400" />
                  <h3 className="text-sm font-semibold text-white">
                    Automated Root Cause Analysis (RCA) & Correlated Evidence
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    disabled={rcaMutation.isPending}
                    onClick={() => rcaMutation.mutate(selectedIncident.incident.id)}
                    className="px-2.5 py-1 text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white rounded flex items-center gap-1.5 transition-colors"
                  >
                    <Zap className="w-3.5 h-3.5" />
                    {rcaMutation.isPending ? "Investigating..." : "Run AI Diagnostic"}
                  </button>
                </div>
              </div>

              {selectedIncident.rca ? (
                <div className="space-y-4 text-xs">
                  <div className="p-3.5 bg-slate-950/70 border border-slate-800 rounded-lg">
                    <div className="text-slate-400 font-semibold mb-1 flex items-center justify-between">
                      <span>PROBABLE ROOT CAUSE:</span>
                      <span className="text-emerald-400 font-mono text-[11px]">
                        Confidence: {(selectedIncident.rca.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-white font-medium leading-relaxed">
                      {selectedIncident.rca.probable_root_cause}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-slate-950/50 border border-slate-800/80 rounded-lg">
                      <span className="text-slate-400 block mb-1">Recommended Remediation:</span>
                      <span className="text-cyan-300 font-mono font-bold">
                        {selectedIncident.rca.recommended_action}
                      </span>
                    </div>
                    <div className="p-3 bg-slate-950/50 border border-slate-800/80 rounded-lg">
                      <span className="text-slate-400 block mb-1">Self-Healing Policy Tier:</span>
                      <span className="text-amber-300 font-bold">
                        Tier {selectedIncident.rca.healing_tier} (
                        {selectedIncident.rca.healing_tier === 1
                          ? "Autonomous Safe Action"
                          : selectedIncident.rca.healing_tier === 2
                          ? "Approval Gate Required"
                          : "Manual Intervention"}
                        )
                      </span>
                    </div>
                  </div>

                  {/* Supporting Evidence */}
                  <div className="p-3 bg-slate-950/40 border border-slate-800/60 rounded-lg">
                    <span className="text-slate-400 font-semibold block mb-1">Telemetry Evidence:</span>
                    <pre className="text-[11px] font-mono text-slate-300 overflow-x-auto bg-slate-950 p-2 rounded">
                      {JSON.stringify(selectedIncident.rca.supporting_evidence, null, 2)}
                    </pre>
                  </div>

                  {/* Incident Lifecycle Transition Controls */}
                  <div className="flex items-center gap-2 pt-2 border-t border-slate-800">
                    <span className="text-slate-400 text-[11px]">Set Status:</span>
                    {["investigating", "rca_completed", "remediating", "resolved", "closed"].map(
                      (st) => (
                        <button
                          key={st}
                          disabled={transitionMutation.isPending}
                          onClick={() =>
                            transitionMutation.mutate({
                              id: selectedIncident.incident.id,
                              status: st,
                            })
                          }
                          className={`px-2 py-0.5 text-[10px] font-mono rounded uppercase border transition-colors ${
                            selectedIncident.incident.status === st
                              ? "bg-indigo-600 text-white border-indigo-500 font-bold"
                              : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
                          }`}
                        >
                          {st}
                        </button>
                      )
                    )}
                  </div>
                </div>
              ) : (
                <div className="p-6 text-center text-slate-400 bg-slate-950/30 rounded-lg">
                  <p className="text-xs">No RCA report generated yet for this incident.</p>
                  <button
                    onClick={() => rcaMutation.mutate(selectedIncident.incident.id)}
                    className="mt-2 px-3 py-1 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-500"
                  >
                    Generate Diagnostic Report
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Service Level Objectives (SLOs) */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-semibold text-white">Reliability & SLO Targets</h3>
              </div>
              <button
                onClick={() => refetchSLOs()}
                className="text-xs text-slate-400 hover:text-white flex items-center gap-1"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Refresh
              </button>
            </div>

            {(!slos || slos.length === 0) ? (
              <div className="text-xs text-slate-400 p-4 bg-slate-950/50 rounded-lg text-center">
                Default SLO target configured at 99.9% availability over rolling 30-day window.
              </div>
            ) : (
              <div className="space-y-3">
                {slos.map((s) => (
                  <div key={s.id} className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-white">{s.name}</span>
                      <span
                        className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase ${
                          s.status === "healthy"
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            : s.status === "at_risk"
                            ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                            : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                        }`}
                      >
                        {s.status}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
                      <span>Current SLI: <strong className="text-emerald-400">{s.current_sli}%</strong> (Target: {s.target_percentage}%)</span>
                      <span>Budget Remaining: <strong className="text-cyan-400">{s.error_budget_remaining_percent}%</strong></span>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-500 ${
                          s.error_budget_remaining_percent > 30 ? "bg-emerald-500" : "bg-rose-500"
                        }`}
                        style={{ width: `${Math.min(100, Math.max(5, s.error_budget_remaining_percent))}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right 1 Col: Probing Controls & Controlled Self-Healing Triggers */}
        <div className="space-y-6">
          {/* Active Probes & Telemetry Sampling */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
              <HeartPulse className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-semibold text-white">Live Synthetic Probes</h3>
            </div>

            <p className="text-xs text-slate-400">
              Execute live health probes and infrastructure telemetry collections on demand.
            </p>

            <div className="space-y-2">
              <button
                disabled={probeMutation.isPending}
                onClick={() => probeMutation.mutate()}
                className="w-full py-2 px-3 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-white rounded-lg flex items-center justify-center gap-2 border border-slate-700 transition-colors"
              >
                <Play className="w-3.5 h-3.5 text-cyan-400" />
                {probeMutation.isPending ? "Probing Application..." : "Execute App Health Probe"}
              </button>

              <button
                disabled={sampleInfraMutation.isPending}
                onClick={() => sampleInfraMutation.mutate()}
                className="w-full py-2 px-3 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-white rounded-lg flex items-center justify-center gap-2 border border-slate-700 transition-colors"
              >
                <Server className="w-3.5 h-3.5 text-indigo-400" />
                {sampleInfraMutation.isPending ? "Sampling Hosts..." : "Sample Host & Worker Metrics"}
              </button>
            </div>

            {probeResult && (
              <div className="p-3 bg-slate-950 border border-cyan-500/30 rounded-lg text-xs space-y-1">
                <div className="text-cyan-400 font-semibold flex items-center justify-between">
                  <span>PROBE RESULT</span>
                  <span className="font-mono text-[11px]">HTTP {probeResult.status_code}</span>
                </div>
                <div className="text-slate-300">
                  Latency: <strong>{probeResult.latency_ms?.toFixed(1)}ms</strong> | Healthy:{" "}
                  <strong>{probeResult.is_healthy ? "YES" : "NO"}</strong>
                </div>
              </div>
            )}
          </div>

          {/* Controlled Self-Healing Triggers */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
              <Zap className="w-4 h-4 text-amber-400" />
              <h3 className="text-sm font-semibold text-white">Controlled Self-Healing</h3>
            </div>

            <div className="space-y-3">
              {/* Tier 1 Actions */}
              <div>
                <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block mb-1.5">
                  Tier 1: Safe Autonomous Actions
                </span>
                <div className="space-y-1.5">
                  <button
                    disabled={healingMutation.isPending}
                    onClick={() =>
                      healingMutation.mutate({
                        action_type: "restart_container",
                        parameters: { service: "application-service" },
                      })
                    }
                    className="w-full text-left px-3 py-2 text-xs bg-slate-950 hover:bg-slate-800/80 text-slate-200 rounded border border-slate-800 flex items-center justify-between transition-colors"
                  >
                    <span>Restart Unhealthy Container</span>
                    <RotateCcw className="w-3.5 h-3.5 text-emerald-400" />
                  </button>

                  <button
                    disabled={healingMutation.isPending}
                    onClick={() =>
                      healingMutation.mutate({
                        action_type: "clear_cache",
                        parameters: { namespace: "global" },
                      })
                    }
                    className="w-full text-left px-3 py-2 text-xs bg-slate-950 hover:bg-slate-800/80 text-slate-200 rounded border border-slate-800 flex items-center justify-between transition-colors"
                  >
                    <span>Flush Stale Cache Keys</span>
                    <RotateCcw className="w-3.5 h-3.5 text-emerald-400" />
                  </button>

                  <button
                    disabled={healingMutation.isPending}
                    onClick={() =>
                      healingMutation.mutate({
                        action_type: "retry_job",
                        parameters: { job_id: "job-failed-01" },
                      })
                    }
                    className="w-full text-left px-3 py-2 text-xs bg-slate-950 hover:bg-slate-800/80 text-slate-200 rounded border border-slate-800 flex items-center justify-between transition-colors"
                  >
                    <span>Retry Poisoned Worker Job</span>
                    <RotateCcw className="w-3.5 h-3.5 text-emerald-400" />
                  </button>
                </div>
              </div>

              {/* Tier 2 Actions */}
              <div>
                <span className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider block mb-1.5">
                  Tier 2: Approval Gate Required
                </span>
                <div className="space-y-1.5">
                  <button
                    disabled={healingMutation.isPending}
                    onClick={() =>
                      healingMutation.mutate({
                        action_type: "scale_service",
                        parameters: { service: "backend-api", target_replicas: 4 },
                      })
                    }
                    className="w-full text-left px-3 py-2 text-xs bg-slate-950 hover:bg-slate-800/80 text-slate-200 rounded border border-slate-800 flex items-center justify-between transition-colors"
                  >
                    <span>Scale Backend Replicas (HPA)</span>
                    <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
                  </button>

                  <button
                    disabled={healingMutation.isPending}
                    onClick={() =>
                      healingMutation.mutate({
                        action_type: "rollback_release",
                        parameters: { reason: "Automated operator rollback" },
                      })
                    }
                    className="w-full text-left px-3 py-2 text-xs bg-slate-950 hover:bg-slate-800/80 text-slate-200 rounded border border-slate-800 flex items-center justify-between transition-colors"
                  >
                    <span>Roll Back Defective Release</span>
                    <RotateCcw className="w-3.5 h-3.5 text-amber-400" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* FinOps Cloud Cost Recommendations */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
              <DollarSign className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-semibold text-white">FinOps Cost Optimization</h3>
            </div>

            {recommendations && recommendations.length > 0 ? (
              <div className="space-y-2">
                {recommendations.slice(0, 3).map((rec, i) => (
                  <div key={i} className="p-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-xs">
                    <div className="font-semibold text-slate-200 flex items-center justify-between">
                      <span>{rec.title}</span>
                      <span className="text-emerald-400 font-mono text-[11px]">
                        Save ${rec.monthly_savings_usd}/mo
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">{rec.action}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-400">All infrastructure assets optimally provisioned.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
