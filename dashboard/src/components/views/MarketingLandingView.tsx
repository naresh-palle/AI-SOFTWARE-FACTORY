"use client";

import React, { useState } from "react";
import {
  Rocket,
  Shield,
  Cpu,
  Bot,
  Zap,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  GitPullRequest,
  Terminal,
  Activity,
  Layers,
  Check,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  ExternalLink,
  Lock,
  Server,
  Code2
} from "lucide-react";
import { ModuleKey } from "../Sidebar";

interface MarketingLandingViewProps {
  onNavigate: (module: ModuleKey) => void;
}

export function MarketingLandingView({ onNavigate }: MarketingLandingViewProps) {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const toggleFaq = (index: number) => {
    setOpenFaq(openFaq === index ? null : index);
  };

  const pricingTiers = [
    {
      name: "Community Free",
      price: "$0",
      period: "forever",
      desc: "For individual developers and open-source contributors exploring autonomous agents.",
      popular: false,
      buttonText: "Get Started Free",
      moduleTarget: "create_project" as ModuleKey,
      features: [
        "1 Active Project",
        "100,000 AI Tokens / month",
        "Core Code Generation (FastAPI and Next.js)",
        "Basic SAST Security Scans",
        "Community Forum Support",
        "Public Sandbox Deployments",
      ],
    },
    {
      name: "Starter",
      price: "$99",
      period: "per month",
      desc: "For fast-moving early stage founders building MVP software with AI velocity.",
      popular: false,
      buttonText: "Activate Starter",
      moduleTarget: "saas_billing" as ModuleKey,
      features: [
        "5 Active Projects",
        "2,000,000 AI Tokens / month",
        "Full 97 Specialist Agent Swarm",
        "Automated GitHub CI/CD and PRs",
        "Docker and Staging Cloud Deployments",
        "Standard Support SLA (24h)",
      ],
    },
    {
      name: "Professional",
      price: "$299",
      period: "per month",
      desc: "For growing engineering teams requiring autonomous releases, monitoring, and maintenance.",
      popular: true,
      buttonText: "Start Pro Trial",
      moduleTarget: "saas_billing" as ModuleKey,
      features: [
        "20 Active Projects",
        "10,000,000 AI Tokens / month",
        "Cloud Execution Engine (Persistent AWS ECS)",
        "Autonomous Self-Healing and Root-Cause Analysis",
        "Dependency CVE Auto-Patching and Maintenance",
        "Priority Support SLA (4h)",
      ],
    },
    {
      name: "Business",
      price: "$799",
      period: "per month",
      desc: "For commercial SaaS platforms requiring high-concurrency cloud workers and deep compliance.",
      popular: false,
      buttonText: "Upgrade to Business",
      moduleTarget: "saas_billing" as ModuleKey,
      features: [
        "Unlimited Projects",
        "50,000,000 AI Tokens / month",
        "Multi-Tenant Organization Workspaces",
        "Custom Domain and Production Deployments",
        "Advanced FinOps and Token Spending Limits",
        "Dedicated Account Engineer (1h SLA)",
      ],
    },
    {
      name: "Enterprise",
      price: "Custom",
      period: "annual billing",
      desc: "For global enterprises requiring custom VPC deployment, dedicated clusters, and compliance guarantees.",
      popular: false,
      buttonText: "Contact Solutions",
      moduleTarget: "saas_billing" as ModuleKey,
      features: [
        "Isolated AWS / Azure VPC Private Cloud",
        "Custom LLM Routing (Bedrock / Vertex / Local)",
        "Custom Compliance (SOC 2, HIPAA, ISO 27001)",
        "Automated Disaster Recovery and 99.99% SLA",
        "24/7/365 Dedicated SRE and On-Call Engineering",
        "Unlimited Compute and Custom Agent Training",
      ],
    },
  ];

  const faqs = [
    {
      q: "How does the Autonomous AI Software Factory differ from traditional code copilot tools?",
      a: "Copilots suggest lines or snippets inside an editor. The AI Software Factory is an autonomous end-to-end engineering workforce: it ingests a natural-language specification, decomposes it into architectural plans, coordinates 97 specialized agents (DB architects, backend, frontend, security, QA), generates production code, executes automated verification in isolated cloud sandboxes, deploys to cloud infrastructure, and autonomously monitors and patches production applications."
    },
    {
      q: "Is my code and intellectual property isolated and secure?",
      a: "Yes. The platform enforces strict multi-tenant isolation at the database, storage, compute, and credential layers. Every customer repository, secret, and execution runs in sandboxed environments with AES-256 encryption at rest and TLS 1.3 in transit. Your code is never used to train global AI models."
    },
    {
      q: "What happens if a generated application encounters an error in production?",
      a: "Our Phase 7 Self-Healing Engine operates 24/7. When an anomaly or exception occurs, the system ingests OpenTelemetry metrics and traces, triggers automated Root-Cause Analysis (RCA), executes authorized recovery actions (such as pod restarts, circuit-breaking, or config rollbacks), and logs complete audit trails."
    },
    {
      q: "Can I retain human approval before changes are pushed to production?",
      a: "Absolutely. The Factory includes a built-in Human-in-the-Loop Governance Center. High-impact operations—such as production deployments, major architectural rewrites, and database migrations—require explicit cryptographic sign-off before execution."
    },
    {
      q: "How does billing and AI token overage management work?",
      a: "Each tier includes a generous token and compute allocation. In the SaaS and FinOps Center, organizations can set hard spending limits and alert thresholds to prevent accidental overages, with real-time visibility into cost per project and per agent."
    }
  ];

  return (
    <div className="space-y-12 pb-16">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-950 via-slate-900 to-slate-950 border border-indigo-500/20 p-8 md:p-12 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-4xl space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold tracking-wide uppercase">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
            Next-Generation Autonomous Engineering Platform
          </div>
          
          <h1 className="text-4xl md:text-5xl font-extrabold text-white tracking-tight leading-tight">
            Turn Plain Language into <br />
            <span className="bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400 bg-clip-text text-transparent">
              Production-Grade SaaS Applications
            </span>
          </h1>

          <p className="text-slate-300 text-base md:text-lg max-w-2xl leading-relaxed">
            The AI Software Factory coordinates 97 specialized autonomous AI agents to design,
            code, test, secure, deploy, and maintain commercial cloud applications—all from a single prompt.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <button
              onClick={() => onNavigate("create_project")}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm px-6 py-3 rounded-xl shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <Rocket className="w-4 h-4" />
              Launch Factory Project
            </button>
            <button
              onClick={() => onNavigate("saas_billing")}
              className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-semibold text-sm px-6 py-3 rounded-xl transition-all"
            >
              <Zap className="w-4 h-4 text-amber-400" />
              View Commercial Plans
            </button>
          </div>

          {/* Key Metrics Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-8 border-t border-slate-800/80">
            <div>
              <div className="text-2xl font-bold text-white">97</div>
              <div className="text-xs text-slate-400">Specialist AI Agents</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-indigo-400">23</div>
              <div className="text-xs text-slate-400">Verification Gates</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-emerald-400">99.9%</div>
              <div className="text-xs text-slate-400">Target Platform SLA</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-400">0% Drift</div>
              <div className="text-xs text-slate-400">Continuous Self-Healing</div>
            </div>
          </div>
        </div>
      </div>

      {/* Autonomous Lifecycle Pipeline */}
      <div className="space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <h2 className="text-2xl font-bold text-white">The Autonomous Software Development Lifecycle</h2>
          <p className="text-sm text-slate-400">
            From natural language requirement to continuous post-release maintenance without local machine dependencies.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { step: "01", title: "Spec Analysis", icon: Terminal, desc: "Decomposes user prompt into SRS and user stories." },
            { step: "02", title: "Architecture", icon: Layers, desc: "Selects microservices, DB schemas and tech stack." },
            { step: "03", title: "Code Swarm", icon: Bot, desc: "97 agents generate full-stack backend and frontend." },
            { step: "04", title: "SAST & QA", icon: Shield, desc: "Executes unit tests, Bandit SAST and compliance." },
            { step: "05", title: "Cloud Release", icon: Rocket, desc: "Deploys Docker containers to ECS / Kubernetes." },
            { step: "06", title: "Self-Healing", icon: Activity, desc: "Continuously fixes CVEs, bugs and runtime errors." },
          ].map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-indigo-500/40 transition-colors group"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono font-bold text-indigo-400">{item.step}</span>
                    <Icon className="w-4 h-4 text-slate-400 group-hover:text-indigo-400 transition-colors" />
                  </div>
                  <h3 className="text-sm font-semibold text-white mb-1">{item.title}</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Core Architectural Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-3">
          <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Lock className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-white">Multi-Tenant Cryptographic Isolation</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Enterprise-grade tenant boundaries. Data, execution workers, credentials, and artifacts are strictly partitioned with scoped row-level security and PBKDF2/Fernet cryptographic standards.
          </p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Server className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-white">Cloud Worker Engine (AWS ECS)</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Persistent execution detached from local machines. Workflows execute asynchronously in resilient cloud worker containers with verifiable state checkpointing and automatic disaster recovery.
          </p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-3">
          <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
            <Activity className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-white">Intelligent Observability & RCA</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Automated OpenTelemetry tracing, AIOps anomaly alerts, and self-healing engine. Detects runtime failures, diagnoses root causes, and executes authorized rollbacks or pod restarts.
          </p>
        </div>
      </div>

      {/* Commercial Pricing Plans */}
      <div className="space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold uppercase">
            Transparent Commercial Tiers
          </div>
          <h2 className="text-3xl font-bold text-white">Predictable Pricing Built for Scale</h2>
          <p className="text-sm text-slate-400">
            Choose the operational plan that aligns with your engineering velocity and infrastructure scale.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {pricingTiers.map((tier, idx) => (
            <div
              key={idx}
              className={`rounded-2xl flex flex-col justify-between p-6 transition-all ${
                tier.popular
                  ? "bg-slate-900 border-2 border-indigo-500 shadow-xl shadow-indigo-500/10 ring-1 ring-indigo-500 relative"
                  : "bg-slate-900/70 border border-slate-800 hover:border-slate-700"
              }`}
            >
              {tier.popular && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-indigo-600 text-white text-[10px] font-bold px-3 py-0.5 rounded-full uppercase tracking-wider">
                  Most Popular
                </span>
              )}

              <div>
                <h3 className="text-lg font-bold text-white">{tier.name}</h3>
                <p className="text-xs text-slate-400 mt-1 min-h-[36px]">{tier.desc}</p>

                <div className="mt-4 mb-6 flex items-baseline gap-1">
                  <span className="text-3xl font-extrabold text-white">{tier.price}</span>
                  <span className="text-xs text-slate-400">/{tier.period}</span>
                </div>

                <ul className="space-y-2.5 border-t border-slate-800/80 pt-4">
                  {tier.features.map((feat, fidx) => (
                    <li key={fidx} className="flex items-start gap-2 text-xs text-slate-300">
                      <Check className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                      <span>{feat}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <button
                onClick={() => onNavigate(tier.moduleTarget)}
                className={`w-full mt-6 py-2.5 px-4 rounded-xl text-xs font-semibold transition-all ${
                  tier.popular
                    ? "bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/30"
                    : "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
                }`}
              >
                {tier.buttonText}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Security & Compliance Credentials */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 space-y-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Shield className="w-5 h-5 text-indigo-400" />
              Enterprise Security & Compliance Standards
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Built to meet stringent regulatory, privacy, and defensive security mandates.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-medium rounded-full border border-emerald-500/20">
              Bandit SAST Verified: 0 High
            </span>
            <span className="px-3 py-1 bg-indigo-500/10 text-indigo-400 text-xs font-medium rounded-full border border-indigo-500/20">
              GDPR & DPDP Ready
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800/80 space-y-1">
            <div className="font-semibold text-slate-200">Data Encryption</div>
            <div className="text-slate-400">AES-256 for secrets & database at rest; TLS 1.3 for all endpoints.</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800/80 space-y-1">
            <div className="font-semibold text-slate-200">Rate Limiting & DoS Defense</div>
            <div className="text-slate-400">Sliding-window IP rate limiting and payload enforcement (10MB max).</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800/80 space-y-1">
            <div className="font-semibold text-slate-200">Disaster Recovery</div>
            <div className="text-slate-400">Automated SHA-256 verified snapshots with RTO 15m & RPO 5m.</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800/80 space-y-1">
            <div className="font-semibold text-slate-200">Privacy & Data Rights</div>
            <div className="text-slate-400">Statutory GDPR DPA and DPDP compliant self-serve data deletion API.</div>
          </div>
        </div>
      </div>

      {/* Frequently Asked Questions */}
      <div className="space-y-6">
        <div className="text-center max-w-xl mx-auto space-y-2">
          <h2 className="text-2xl font-bold text-white flex items-center justify-center gap-2">
            <HelpCircle className="w-5 h-5 text-indigo-400" />
            Frequently Asked Questions
          </h2>
          <p className="text-xs text-slate-400">
            Common queries about our autonomous architecture, licensing, and security.
          </p>
        </div>

        <div className="max-w-3xl mx-auto space-y-3">
          {faqs.map((faq, idx) => (
            <div
              key={idx}
              className="border border-slate-800 bg-slate-900/60 rounded-xl overflow-hidden transition-all"
            >
              <button
                onClick={() => toggleFaq(idx)}
                className="w-full flex items-center justify-between p-4 text-left font-medium text-slate-200 text-sm hover:text-white hover:bg-slate-800/40 transition-colors"
              >
                <span>{faq.q}</span>
                {openFaq === idx ? (
                  <ChevronUp className="w-4 h-4 text-indigo-400 flex-shrink-0 ml-2" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-slate-400 flex-shrink-0 ml-2" />
                )}
              </button>
              {openFaq === idx && (
                <div className="p-4 pt-0 text-xs text-slate-400 leading-relaxed border-t border-slate-800/50 bg-slate-950/30">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Final Call to Action */}
      <div className="text-center bg-gradient-to-r from-indigo-900/40 via-purple-900/40 to-slate-900/40 border border-indigo-500/20 rounded-2xl p-10 space-y-4">
        <h2 className="text-2xl md:text-3xl font-bold text-white">Ready to Accelerate Software Engineering?</h2>
        <p className="text-xs md:text-sm text-slate-300 max-w-xl mx-auto">
          Start autonomously generating full-stack software with 97 AI agents, automated CI/CD releases, and self-healing operations today.
        </p>
        <div className="pt-2 flex justify-center gap-4">
          <button
            onClick={() => onNavigate("create_project")}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-6 py-3 rounded-xl shadow-lg shadow-indigo-600/30 transition-all"
          >
            <Rocket className="w-4 h-4" />
            Start Developing Now
          </button>
          <button
            onClick={() => onNavigate("overview")}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs px-6 py-3 rounded-xl border border-slate-700 transition-all"
          >
            Explore Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}

export default MarketingLandingView;
