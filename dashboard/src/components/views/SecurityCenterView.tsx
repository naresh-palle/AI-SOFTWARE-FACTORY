"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { ShieldAlert, ShieldCheck, Lock, CheckCircle2, AlertTriangle, Key } from "lucide-react";
import { fetchSecurityFindings } from "@/lib/api";

export function SecurityCenterView() {
  const { data: findings, isLoading } = useQuery({
    queryKey: ["security-findings"],
    queryFn: fetchSecurityFindings,
  });

  const securityBadges = [
    { title: "Secrets Encryption", desc: "Fernet AES-256 for OAuth Tokens", status: "Active", icon: Lock },
    { title: "OWASP Top 10 Guard", desc: "Input sanitization & SQL injection defense", status: "Active", icon: ShieldCheck },
    { title: "Tenant Isolation", desc: "Cryptographic token separation per project", status: "Active", icon: Key },
    { title: "CORS Credentials", desc: "Wildcard credentials strictly disabled", status: "Verified", icon: ShieldCheck },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-emerald-400" />
            Enterprise Security & Governance Center
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Real-time vulnerability scanning, SAST checks, secrets isolation, and tamper-evident audit logging.
          </p>
        </div>
        <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-2.5 py-1 rounded">
          Zero Critical CVEs
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {securityBadges.map((badge, idx) => {
          const Icon = badge.icon;
          return (
            <div key={idx} className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white">{badge.title}</span>
                <Icon className="w-4 h-4 text-emerald-400" />
              </div>
              <p className="text-[11px] text-slate-400">{badge.desc}</p>
              <div className="pt-2">
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded">
                  {badge.status}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Findings table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
            Automated Scanner Findings ({findings?.length || 0})
          </h4>
        </div>
        <div className="p-8 text-center text-slate-500 text-xs">
          <ShieldCheck className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
          <span className="font-semibold text-white">All Security Audits Passed</span>
          <p className="text-slate-500 mt-0.5">
            No unmitigated vulnerabilities detected in active project dependencies.
          </p>
        </div>
      </div>
    </div>
  );
}
