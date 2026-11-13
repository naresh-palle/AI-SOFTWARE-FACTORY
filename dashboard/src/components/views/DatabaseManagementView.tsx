"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Database, CheckCircle2, Server, Table } from "lucide-react";
import { fetchDatabaseStatus } from "@/lib/api";

export function DatabaseManagementView() {
  const { data: dbStatus, isLoading } = useQuery({
    queryKey: ["db-status"],
    queryFn: fetchDatabaseStatus,
  });

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-emerald-400" />
            Central Factory Database Management
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Storage engine status, entity counts, schema migrations, and relational integrity.
          </p>
        </div>
        <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-2.5 py-1 rounded">
          {dbStatus?.connection || "Healthy"}
        </span>
      </div>

      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-4">
        <h4 className="text-xs font-bold text-white uppercase tracking-wider">Engine Configuration</h4>
        <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
          <span className="text-xs text-slate-400">Database Driver & Type</span>
          <span className="text-xs font-mono font-bold text-cyan-400">
            {dbStatus?.engine || "PostgreSQL / SQLite Dual Driver"}
          </span>
        </div>
      </div>

      {dbStatus?.tables && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-800">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider">
              Entity Table Population
            </h4>
          </div>
          <div className="divide-y divide-slate-800/60">
            {Object.entries(dbStatus.tables).map(([table, count]) => (
              <div key={table} className="px-5 py-3 flex items-center justify-between text-xs">
                <span className="font-mono text-slate-300 capitalize">{table}</span>
                <span className="font-mono font-bold text-indigo-400">{count} records</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
