"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  RotateCcw,
  Check,
  X,
} from "lucide-react";
import { fetchProjectApprovals, respondApproval, fetchProjects } from "@/lib/api";

interface ApprovalCenterViewProps {
  projectId: string | null;
  onRefreshProject?: () => void;
}

export function ApprovalCenterView({ projectId, onRefreshProject }: ApprovalCenterViewProps) {
  const [decidingId, setDecidingId] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const { data: approvals, isLoading, refetch } = useQuery({
    queryKey: ["project-approvals", projectId],
    queryFn: () => (projectId ? fetchProjectApprovals(projectId) : []),
    enabled: !!projectId,
    refetchInterval: 3000,
  });

  const handleDecision = async (approvalId: string, decision: "approved" | "rejected") => {
    setDecidingId(approvalId);
    setActionMessage(null);
    try {
      await respondApproval(approvalId, decision, notes);
      setActionMessage(`Approval successfully marked as ${decision}.`);
      setNotes("");
      refetch();
      if (onRefreshProject) onRefreshProject();
    } catch (err: any) {
      setActionMessage(`Error: ${err.message || "Failed to record decision"}`);
    } finally {
      setDecidingId(null);
    }
  };

  const pendingApprovals = (approvals || []).filter((a) => a.status === "pending");
  const pastApprovals = (approvals || []).filter((a) => a.status !== "pending");

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Overview Banner */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-amber-400" />
            Human-in-the-Loop Governance Gate
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Mandatory approval checkpoints for production deployments, external credentials, and paid third-party platforms.
          </p>
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-500 font-mono">Pending Decisions</span>
          <p className="text-2xl font-bold text-amber-400">{pendingApprovals.length}</p>
        </div>
      </div>

      {actionMessage && (
        <div className="bg-indigo-950/40 border border-indigo-800/60 p-3 rounded-lg text-xs text-indigo-300">
          {actionMessage}
        </div>
      )}

      {/* Pending Approvals */}
      <div className="space-y-4">
        <h4 className="text-xs font-bold text-white uppercase tracking-wider">
          Action Required ({pendingApprovals.length})
        </h4>

        {isLoading ? (
          <div className="bg-slate-900 border border-slate-800 p-8 rounded-xl text-center text-xs text-slate-500">
            Checking approval checkpoints...
          </div>
        ) : pendingApprovals.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 p-8 rounded-xl text-center text-xs text-slate-400">
            <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
            <span className="font-semibold text-white">No Pending Approvals</span>
            <p className="text-slate-500 mt-0.5">
              All governance gates are cleared. Autonomous execution can continue.
            </p>
          </div>
        ) : (
          pendingApprovals.map((app) => (
            <div
              key={app.id}
              className="bg-slate-900 border border-amber-500/40 p-5 rounded-xl space-y-4 shadow-lg shadow-amber-950/20"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 bg-amber-500 text-slate-950 text-[10px] font-bold rounded">
                      STAGE {app.stage}
                    </span>
                    <span className="font-mono text-xs text-amber-300 font-semibold uppercase">
                      {app.action_type.replace("_", " ")}
                    </span>
                  </div>
                  <h5 className="text-sm font-bold text-white mt-1.5">{app.description}</h5>
                </div>
                <span className="text-[11px] font-mono text-slate-500">
                  {new Date(app.created_at).toLocaleTimeString()}
                </span>
              </div>

              {/* Reviewer Note Input */}
              <div>
                <input
                  type="text"
                  placeholder="Optional decision notes (e.g. Approved production release after QA verification)"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 font-sans"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  onClick={() => handleDecision(app.id, "rejected")}
                  disabled={decidingId === app.id}
                  className="flex items-center gap-1.5 bg-slate-800 hover:bg-rose-950/60 hover:text-rose-400 text-slate-300 text-xs font-semibold px-4 py-1.5 rounded-lg transition-colors border border-slate-700"
                >
                  <X className="w-3.5 h-3.5" />
                  <span>Reject</span>
                </button>

                <button
                  onClick={() => handleDecision(app.id, "approved")}
                  disabled={decidingId === app.id}
                  className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold px-4 py-1.5 rounded-lg transition-colors shadow-md shadow-emerald-950"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Approve & Proceed</span>
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* History */}
      {pastApprovals.length > 0 && (
        <div className="space-y-3 pt-6 border-t border-slate-800">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Approval History ({pastApprovals.length})
          </h4>
          <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800/60 overflow-hidden">
            {pastApprovals.map((pa) => (
              <div key={pa.id} className="p-4 flex items-center justify-between text-xs">
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`font-mono text-[10px] font-bold px-1.5 py-0.5 rounded capitalize ${
                        pa.status === "approved"
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : "bg-rose-950 text-rose-400 border border-rose-800"
                      }`}
                    >
                      {pa.status}
                    </span>
                    <span className="text-white font-medium">{pa.description}</span>
                  </div>
                  {pa.notes && <p className="text-[11px] text-slate-500 mt-1 font-sans">{pa.notes}</p>}
                </div>
                <span className="text-[10px] font-mono text-slate-500">
                  {pa.decided_at ? new Date(pa.decided_at).toLocaleString() : ""}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
