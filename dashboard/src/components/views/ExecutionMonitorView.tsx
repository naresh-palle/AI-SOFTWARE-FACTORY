"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  Play,
  RotateCcw,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileCode,
  ShieldAlert,
  Cpu,
  Layers,
  Sparkles,
} from "lucide-react";
import { fetchProject, executeProject, fetchProjectTasks } from "@/lib/api";

interface ExecutionMonitorViewProps {
  projectId: string | null;
  onNavigateToApprovals: () => void;
}

export function ExecutionMonitorView({ projectId, onNavigateToApprovals }: ExecutionMonitorViewProps) {
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionMessage, setExecutionMessage] = useState<string | null>(null);

  const { data: projectState, isLoading, refetch } = useQuery({
    queryKey: ["project-state", projectId],
    queryFn: () => (projectId ? fetchProject(projectId) : null),
    enabled: !!projectId,
    refetchInterval: 3000, // Poll every 3 seconds for live execution
  });

  const { data: tasks } = useQuery({
    queryKey: ["project-tasks", projectId],
    queryFn: () => (projectId ? fetchProjectTasks(projectId) : []),
    enabled: !!projectId,
  });

  const handleExecuteNext = async () => {
    if (!projectId || !projectState) return;
    setIsExecuting(true);
    setExecutionMessage(null);
    try {
      const nextStage = Math.min(projectState.current_stage + 1, 23);
      await executeProject(projectId, nextStage);
      refetch();
    } catch (err: any) {
      setExecutionMessage(err.message || "Failed to execute stage");
    } finally {
      setIsExecuting(false);
    }
  };

  const handleRunFull = async () => {
    if (!projectId) return;
    setIsExecuting(true);
    setExecutionMessage(null);
    try {
      await executeProject(projectId, 23);
      refetch();
    } catch (err: any) {
      setExecutionMessage(err.message || "Pipeline execution halted");
    } finally {
      setIsExecuting(false);
    }
  };

  if (!projectId) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
        <Activity className="w-8 h-8 text-slate-600 mx-auto mb-3" />
        <h4 className="text-sm font-bold text-white">No Project Selected</h4>
        <p className="text-xs text-slate-500 mt-1">
          Select an active project from the top bar dropdown or create a new project.
        </p>
      </div>
    );
  }

  const stagesList = projectState?.stages ? Object.values(projectState.stages) : [];
  const completedStagesCount = stagesList.filter((s) => s.status === "completed").length;
  const progressPercent = Math.round((completedStagesCount / 23) * 100);

  return (
    <div className="space-y-6">
      {/* Top Project Status Banner */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-white">{projectState?.project_name}</h3>
            <span className="font-mono text-[10px] text-slate-500 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
              {projectId}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 line-clamp-1">
            {projectState?.requirement_text}
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={handleExecuteNext}
            disabled={isExecuting || projectState?.is_completed}
            className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-white text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors border border-slate-700"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Step Next Stage</span>
          </button>

          <button
            onClick={handleRunFull}
            disabled={isExecuting || projectState?.is_completed}
            className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-bold px-4 py-2 rounded-lg transition-colors shadow-md shadow-indigo-950"
          >
            {isExecuting ? (
              <>
                <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                <span>Running Pipeline...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Run Full Pipeline (1..23)</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Progress & Alert Bar */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-3">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-slate-300">
            Pipeline Progression: Stage {projectState?.current_stage || 1} of 23
          </span>
          <span className="font-mono text-indigo-400 font-bold">{progressPercent}% Completed</span>
        </div>
        <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden border border-slate-800">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 transition-all duration-500 rounded-full"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Approval Alert if blocked */}
        {projectState?.pending_approvals && projectState.pending_approvals.length > 0 && (
          <div className="bg-amber-500/10 border border-amber-500/30 p-3 rounded-lg flex items-center justify-between mt-3">
            <div className="flex items-center gap-2 text-xs text-amber-300 font-medium">
              <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <span>
                Pipeline paused at Stage 20: Production Deployment Gate requires mandatory human approval.
              </span>
            </div>
            <button
              onClick={onNavigateToApprovals}
              className="bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs px-3 py-1 rounded-md transition-colors"
            >
              Review Gate
            </button>
          </div>
        )}
      </div>

      {/* 23 Stages Detailed Grid */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
            Development Pipeline Lifecycle (Stages 1..23)
          </h4>
          <span className="text-[11px] font-mono text-slate-400">
            Strict Verifiable Evidence Enforced
          </span>
        </div>

        <div className="divide-y divide-slate-800/60 max-h-[500px] overflow-y-auto">
          {stagesList.map((st) => {
            const isCompleted = st.status === "completed";
            const isCurrent = st.stage_number === projectState?.current_stage;
            const isBlocked = st.status === "blocked_on_approval";

            return (
              <div
                key={st.stage_number}
                className={`p-4 flex items-start justify-between gap-4 transition-colors ${
                  isCurrent ? "bg-indigo-950/20" : "hover:bg-slate-800/20"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">
                    {isCompleted ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    ) : isBlocked ? (
                      <AlertTriangle className="w-5 h-5 text-amber-400 animate-pulse" />
                    ) : isCurrent ? (
                      <RotateCcw className="w-5 h-5 text-indigo-400 animate-spin" />
                    ) : (
                      <Clock className="w-5 h-5 text-slate-600" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-400">
                        Stage {st.stage_number}:
                      </span>
                      <h5 className="text-xs font-bold text-white">{st.title}</h5>
                      <span
                        className={`text-[10px] font-mono px-1.5 py-0.5 rounded capitalize ${
                          isCompleted
                            ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                            : isBlocked
                            ? "bg-amber-950 text-amber-400 border border-amber-800"
                            : isCurrent
                            ? "bg-indigo-950 text-indigo-400 border border-indigo-800"
                            : "bg-slate-950 text-slate-500"
                        }`}
                      >
                        {st.status.replace("_", " ")}
                      </span>
                    </div>

                    {/* Execution Evidence Details */}
                    {st.execution_evidence && st.execution_evidence.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {st.execution_evidence.map((ev, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center gap-1 text-[10px] text-slate-300 bg-slate-950 border border-slate-800 px-2 py-0.5 rounded font-mono"
                          >
                            <FileCode className="w-3 h-3 text-cyan-400" />
                            {ev}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
