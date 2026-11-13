"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { GitBranch, GitPullRequest, GitCommit, ExternalLink, ShieldCheck } from "lucide-react";
import { fetchProjectGithub } from "@/lib/api";

export function GithubView({ projectId }: { projectId: string | null }) {
  const { data: github, isLoading } = useQuery({
    queryKey: ["project-github", projectId],
    queryFn: () => (projectId ? fetchProjectGithub(projectId) : null),
    enabled: !!projectId,
  });

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-indigo-400" />
            GitHub Version Control Integration
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Automated repository provisioning, feature branches, pull requests, and CI/CD pipelines.
          </p>
        </div>
        <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-2.5 py-1 rounded">
          {github?.connected ? "Connected" : "Local Workspace Mode"}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">Default Branch</span>
          <p className="text-sm font-bold text-white mt-1 font-mono">{github?.default_branch || "main"}</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">Working Branch</span>
          <p className="text-sm font-bold text-cyan-400 mt-1 font-mono">{github?.current_branch || "main"}</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">Latest Commit</span>
          <p className="text-sm font-bold text-indigo-400 mt-1 font-mono truncate">
            {github?.latest_commit_hash || "Initial Workspace Commit"}
          </p>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-3">
        <h4 className="text-xs font-bold text-white uppercase tracking-wider">Repository Details</h4>
        <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between">
          <div className="font-mono text-xs text-slate-300">
            {github?.repo_url || "https://github.com/naresh-palle/AI-SOFTWARE-FACTORY.git"}
          </div>
          <a
            href={github?.repo_url || "https://github.com/naresh-palle/AI-SOFTWARE-FACTORY.git"}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium"
          >
            <span>View on GitHub</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    </div>
  );
}
