"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, PlayCircle, FileText, CheckCircle, XCircle } from "lucide-react";
import { fetchQAResults } from "@/lib/api";

export function QACenterView() {
  const { data: qaResults, isLoading } = useQuery({
    queryKey: ["qa-results"],
    queryFn: fetchQAResults,
  });

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-indigo-400" />
            Quality Assurance & Verification Center
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Automated test suites (Pytest, Playwright UI, Appium, API contract assertions).
          </p>
        </div>
        <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-2.5 py-1 rounded">
          Quality Gate: Enforced
        </span>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 font-semibold">Test Suite</th>
              <th className="py-3 px-4 font-semibold">Total Tests</th>
              <th className="py-3 px-4 font-semibold">Passed</th>
              <th className="py-3 px-4 font-semibold">Failed</th>
              <th className="py-3 px-4 font-semibold">Evidence Report</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-500">
                  Loading QA reports...
                </td>
              </tr>
            ) : !qaResults || qaResults.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-500">
                  No test runs recorded yet.
                </td>
              </tr>
            ) : (
              qaResults.map((r) => (
                <tr key={r.id} className="hover:bg-slate-800/30">
                  <td className="py-3 px-4 font-bold text-white uppercase font-mono">{r.test_suite}</td>
                  <td className="py-3 px-4 font-mono">{r.total_tests}</td>
                  <td className="py-3 px-4 font-mono text-emerald-400 font-bold">{r.passed_tests}</td>
                  <td className="py-3 px-4 font-mono text-rose-400">{r.failed_tests}</td>
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-400 truncate max-w-xs">
                    {r.evidence_path || "Verified by QA Architect"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
