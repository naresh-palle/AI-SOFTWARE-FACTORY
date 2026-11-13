"use client";

import React, { useState } from "react";
import {
  Sparkles,
  ArrowRight,
  CheckCircle,
  Cpu,
  Layers,
  Bot,
  DollarSign,
  AlertCircle,
  Play,
  RotateCcw,
} from "lucide-react";
import { analyzeRequirement, createProject, executeProject } from "@/lib/api";

interface CreateProjectViewProps {
  onProjectCreated: (projectId: string) => void;
}

export function CreateProjectView({ onProjectCreated }: CreateProjectViewProps) {
  // Form state
  const [name, setName] = useState("");
  const [requirementText, setRequirementText] = useState("");
  const [targetPlatform, setTargetPlatform] = useState("fullstack"); // website, android, ios, fullstack
  const [preferredCloud, setPreferredCloud] = useState("AWS");
  const [budgetConstraint, setBudgetConstraint] = useState("Standard");
  const [executionMode, setExecutionMode] = useState("autonomous");

  // Analysis & Submission states
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState<any>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!requirementText || requirementText.trim().length < 5) {
      setAnalysisError("Please provide a software requirement with at least 5 characters.");
      return;
    }
    setIsAnalyzing(true);
    setAnalysisError(null);
    try {
      const plan = await analyzeRequirement(requirementText, targetPlatform);
      setAnalysisResult(plan);
      if (!name) {
        setName(plan.project_title.replace("Autonomous Project: ", "").slice(0, 30));
      }
    } catch (err: any) {
      setAnalysisError(err.message || "Failed to analyze requirement");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCreateAndExecute = async () => {
    if (!name.trim()) {
      setSubmitError("Please specify a project name.");
      return;
    }
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const created = await createProject({
        name,
        requirement_text: requirementText,
        platform_target: targetPlatform,
        execution_mode: executionMode,
      });
      setSubmitSuccess(created);
      // Trigger execution pipeline immediately in background
      await executeProject(created.project_id, 20); // Execute up to Stage 20 (Approval gate)
      onProjectCreated(created.project_id);
    } catch (err: any) {
      setSubmitError(err.message || "Failed to instantiate project");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Input Section */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-6">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            Autonomous Project Architect
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Enter your application requirement in natural language. Our Technology Selection and Agent Assignment Engine will evaluate constraints, select tech stacks, and activate specialist agents.
          </p>
        </div>

        {/* Inputs */}
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Project Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. NextGen E-Commerce & Subscription SaaS"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-medium"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Software Requirement (Natural Language)
            </label>
            <textarea
              rows={4}
              value={requirementText}
              onChange={(e) => setRequirementText(e.target.value)}
              placeholder="e.g. Build an e-commerce website and mobile application with payment gateway, user authentication, order management, WhatsApp alerts, and an admin dashboard."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 leading-relaxed font-sans"
            />
          </div>

          {/* Options Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
            <div>
              <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                Platform Targets
              </label>
              <select
                value={targetPlatform}
                onChange={(e) => setTargetPlatform(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none"
              >
                <option value="fullstack">Website + Android + iOS</option>
                <option value="website">Website Only</option>
                <option value="android">Android Only</option>
                <option value="ios">iOS Only</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                Preferred Cloud
              </label>
              <select
                value={preferredCloud}
                onChange={(e) => setPreferredCloud(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none"
              >
                <option value="AWS">AWS (ECS, RDS, S3)</option>
                <option value="GCP">Google Cloud (GKE, Cloud SQL)</option>
                <option value="Azure">Microsoft Azure</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                Budget Model
              </label>
              <select
                value={budgetConstraint}
                onChange={(e) => setBudgetConstraint(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none"
              >
                <option value="Standard">Standard FinOps</option>
                <option value="Cost-Optimized">Cost-Optimized / Serverless</option>
                <option value="High-Performance">High-Throughput Enterprise</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                Execution Mode
              </label>
              <select
                value={executionMode}
                onChange={(e) => setExecutionMode(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none"
              >
                <option value="autonomous">Autonomous (Gated at Prod)</option>
                <option value="semi-autonomous">Semi-Autonomous</option>
                <option value="assisted">Assisted (Step-by-Step)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-800">
          {analysisError && (
            <span className="text-xs text-rose-400 flex items-center gap-1.5">
              <AlertCircle className="w-4 h-4" />
              {analysisError}
            </span>
          )}
          {!analysisError && <span className="text-xs text-slate-500">Ready to analyze architecture</span>}

          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors"
          >
            {isAnalyzing ? (
              <>
                <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                <span>Evaluating Architecture...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Analyze Requirements</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Analysis Result Card */}
      {analysisResult && (
        <div className="bg-slate-900 border border-indigo-500/30 p-6 rounded-xl space-y-6 shadow-xl shadow-indigo-950/20 animate-in fade-in duration-300">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[11px] font-bold text-indigo-400 uppercase tracking-wider">
                Dynamic Architecture Decision
              </span>
              <h4 className="text-lg font-bold text-white mt-0.5">
                {analysisResult.project_title}
              </h4>
            </div>
            <div className="text-right">
              <span className="text-xs text-slate-400">Estimated Monthly Cloud Cost</span>
              <p className="text-lg font-bold text-emerald-400">
                ${analysisResult.estimated_monthly_cost_usd?.toFixed(2) || "35.00"}
              </p>
            </div>
          </div>

          {/* Tech Decision Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800">
              <span className="text-[10px] font-semibold text-slate-400 uppercase">Frontend</span>
              <p className="text-xs font-bold text-indigo-300 mt-1">
                {analysisResult.technology_stack?.frontend}
              </p>
            </div>
            <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800">
              <span className="text-[10px] font-semibold text-slate-400 uppercase">Backend</span>
              <p className="text-xs font-bold text-cyan-300 mt-1">
                {analysisResult.technology_stack?.backend}
              </p>
            </div>
            <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800">
              <span className="text-[10px] font-semibold text-slate-400 uppercase">Database & Cache</span>
              <p className="text-xs font-bold text-emerald-300 mt-1">
                {analysisResult.technology_stack?.database} {analysisResult.technology_stack?.cache && `+ ${analysisResult.technology_stack.cache}`}
              </p>
            </div>
          </div>

          {/* Selected Agents Pills */}
          <div>
            <h5 className="text-xs font-bold text-slate-300 mb-2.5 flex items-center gap-1.5">
              <Bot className="w-4 h-4 text-cyan-400" />
              Assigned Specialist Agents ({analysisResult.selected_agent_roles?.length || 0})
            </h5>
            <div className="flex flex-wrap gap-1.5">
              {analysisResult.selected_agent_roles?.map((role: string, idx: number) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded-md bg-slate-950 border border-slate-800 text-[11px] text-slate-300 font-medium"
                >
                  {role}
                </span>
              ))}
            </div>
          </div>

          {/* Submit & Execute Footer */}
          <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
            {submitError && (
              <span className="text-xs text-rose-400 flex items-center gap-1">
                <AlertCircle className="w-4 h-4" />
                {submitError}
              </span>
            )}
            {!submitError && (
              <span className="text-xs text-emerald-400 flex items-center gap-1">
                <CheckCircle className="w-4 h-4" />
                Architecture validated & ready for autonomous build
              </span>
            )}

            <button
              onClick={handleCreateAndExecute}
              disabled={isSubmitting}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-bold px-5 py-2.5 rounded-lg transition-colors shadow-lg shadow-emerald-950/40"
            >
              {isSubmitting ? (
                <>
                  <RotateCcw className="w-4 h-4 animate-spin" />
                  <span>Instantiating Factory Pipeline...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  <span>Confirm & Run Project</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
