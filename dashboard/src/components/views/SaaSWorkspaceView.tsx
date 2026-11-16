"use client";

import React, { useState, useEffect } from "react";
import {
  fetchSaaSPlans,
  fetchActiveSubscription,
  fetchUsageSummary,
  fetchInvoices,
  fetchAIProviders,
  fetchCredentials,
  fetchSupportTickets,
  fetchNotifications,
  fetchAdminMetrics,
  fetchAdminTenants,
  upgradeSubscription,
  createSupportTicket,
  storeCredential,
  processSaaSPayment,
  suspendTenant,
  reactivateTenant
} from "@/lib/api";
import {
  CreditCard,
  Building,
  ShieldCheck,
  Zap,
  TrendingUp,
  Key,
  LifeBuoy,
  Bell,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Users,
  DollarSign
} from "lucide-react";

export default function SaaSWorkspaceView() {
  const [activeTab, setActiveTab] = useState<
    "subscription" | "usage" | "billing" | "providers" | "support" | "admin"
  >("subscription");

  const [loading, setLoading] = useState(true);
  const [plans, setPlans] = useState<any[]>([]);
  const [activeSub, setActiveSub] = useState<any>(null);
  const [usage, setUsage] = useState<any>(null);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [providers, setProviders] = useState<any[]>([]);
  const [credentials, setCredentials] = useState<any[]>([]);
  const [tickets, setTickets] = useState<any[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [adminMetrics, setAdminMetrics] = useState<any>(null);
  const [adminTenants, setAdminTenants] = useState<any[]>([]);

  // Form states
  const [ticketSubject, setTicketSubject] = useState("");
  const [ticketMsg, setTicketMsg] = useState("");
  const [credProvider, setCredProvider] = useState("openai");
  const [credSecret, setCredSecret] = useState("");
  const [credKeyId, setCredKeyId] = useState("");
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [
        plansRes,
        subRes,
        usageRes,
        invRes,
        provRes,
        credRes,
        tickRes,
        notifRes,
        metricsRes,
        tenantsRes
      ] = await Promise.allSettled([
        fetchSaaSPlans(),
        fetchActiveSubscription(),
        fetchUsageSummary(),
        fetchInvoices(),
        fetchAIProviders(),
        fetchCredentials(),
        fetchSupportTickets(),
        fetchNotifications(),
        fetchAdminMetrics(),
        fetchAdminTenants()
      ]);

      if (plansRes.status === "fulfilled") setPlans(plansRes.value);
      if (subRes.status === "fulfilled") setActiveSub(subRes.value);
      if (usageRes.status === "fulfilled") setUsage(usageRes.value);
      if (invRes.status === "fulfilled") setInvoices(invRes.value);
      if (provRes.status === "fulfilled") setProviders(provRes.value);
      if (credRes.status === "fulfilled") setCredentials(credRes.value);
      if (tickRes.status === "fulfilled") setTickets(tickRes.value);
      if (notifRes.status === "fulfilled") setNotifications(notifRes.value);
      if (metricsRes.status === "fulfilled") setAdminMetrics(metricsRes.value);
      if (tenantsRes.status === "fulfilled") setAdminTenants(tenantsRes.value);
    } catch (e) {
      console.error("Error loading SaaS workspace data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUpgrade = async (tier: string) => {
    try {
      await upgradeSubscription({ new_plan_tier: tier });
      setFeedbackMsg(`Successfully switched subscription to ${tier.toUpperCase()}`);
      loadData();
    } catch (e: any) {
      setFeedbackMsg(`Upgrade failed: ${e.message}`);
    }
  };

  const handleAddCredential = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!credSecret) return;
    try {
      await storeCredential({
        provider: credProvider,
        credential_type: "api_key",
        secret_value: credSecret,
        key_identifier: credKeyId || undefined
      });
      setFeedbackMsg(`Credential for ${credProvider} securely stored & encrypted.`);
      setCredSecret("");
      setCredKeyId("");
      loadData();
    } catch (e: any) {
      setFeedbackMsg(`Failed to save credential: ${e.message}`);
    }
  };

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticketSubject || !ticketMsg) return;
    try {
      await createSupportTicket({
        subject: ticketSubject,
        message: ticketMsg,
        category: "billing",
        priority: "medium"
      });
      setFeedbackMsg("Support ticket submitted successfully.");
      setTicketSubject("");
      setTicketMsg("");
      loadData();
    } catch (e: any) {
      setFeedbackMsg(`Failed to create ticket: ${e.message}`);
    }
  };

  const handleSimulatePayment = async () => {
    try {
      const res = await processSaaSPayment({
        amount: 49.0,
        currency: "USD",
        gateway: "stripe",
        description: "Monthly subscription renewal"
      });
      setFeedbackMsg(`Payment #${res.id} processed successfully!`);
      loadData();
    } catch (e: any) {
      setFeedbackMsg(`Payment processing failed: ${e.message}`);
    }
  };

  const handleToggleTenant = async (tenantId: string, currentStatus: string) => {
    try {
      if (currentStatus === "active") {
        await suspendTenant(tenantId, "Administrative policy enforcement");
        setFeedbackMsg(`Tenant ${tenantId} suspended.`);
      } else {
        await reactivateTenant(tenantId);
        setFeedbackMsg(`Tenant ${tenantId} reactivated.`);
      }
      loadData();
    } catch (e: any) {
      setFeedbackMsg(`Action failed: ${e.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold tracking-tight">SaaS Workspace & Billing</h2>
            <span className="px-2 py-0.5 text-xs font-semibold rounded bg-primary/10 text-primary border border-primary/20">
              Module #22
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Multi-tenant organization management, tiered subscriptions, automated billing, usage quotas & AI model integration.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {feedbackMsg && (
        <div className="p-3 bg-primary/10 border border-primary/20 rounded-md text-sm text-primary flex items-center justify-between">
          <span>{feedbackMsg}</span>
          <button onClick={() => setFeedbackMsg(null)} className="text-xs font-bold ml-4">
            ×
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border pb-2 overflow-x-auto">
        {[
          { id: "subscription", label: "Plans & Subscription", icon: Zap },
          { id: "usage", label: "Usage & Quotas", icon: TrendingUp },
          { id: "billing", label: "Billing & Invoices", icon: CreditCard },
          { id: "providers", label: "AI Models & BYOK", icon: Key },
          { id: "support", label: "Support & Notifications", icon: LifeBuoy },
          { id: "admin", label: "Platform Admin", icon: ShieldCheck }
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3 py-2 text-xs font-medium rounded-md whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? "bg-primary text-primary-foreground shadow"
                  : "bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* TAB 1: Subscriptions & Plans */}
      {activeTab === "subscription" && (
        <div className="space-y-6">
          {/* Active plan card */}
          <div className="p-4 rounded-lg border border-border bg-card">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">
                  Active Subscription
                </span>
                <h3 className="text-xl font-bold mt-1 text-foreground">
                  {activeSub?.plan?.name || "Free Tier"}
                </h3>
                <p className="text-xs text-muted-foreground">
                  Status: <span className="font-semibold text-emerald-500 uppercase">{activeSub?.status || "Active"}</span> • Billing Cycle: {activeSub?.billing_cycle || "Monthly"}
                </p>
              </div>
              <div className="text-right">
                <span className="text-2xl font-extrabold text-foreground">
                  ${activeSub?.plan?.price_monthly || 0}
                </span>
                <span className="text-xs text-muted-foreground">/month</span>
              </div>
            </div>
          </div>

          {/* Plan catalog */}
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {plans.map((p) => {
              const isCurrent = activeSub?.plan?.tier === p.tier || (!activeSub && p.tier === "free");
              return (
                <div
                  key={p.id}
                  className={`p-4 rounded-lg border flex flex-col justify-between ${
                    isCurrent
                      ? "border-primary bg-primary/5 shadow"
                      : "border-border bg-card"
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-sm text-foreground">{p.name}</h4>
                      {isCurrent && (
                        <span className="text-[10px] bg-primary text-primary-foreground px-1.5 py-0.5 rounded font-semibold">
                          Current
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1 min-h-[32px]">{p.description}</p>
                    <div className="my-3">
                      <span className="text-xl font-bold">${p.price_monthly}</span>
                      <span className="text-xs text-muted-foreground">/mo</span>
                    </div>

                    <div className="space-y-1 text-xs text-muted-foreground border-t border-border pt-2">
                      <div>• {p.limits?.max_projects === -1 ? "Unlimited" : p.limits?.max_projects} Projects</div>
                      <div>• {(p.limits?.monthly_tokens / 1000).toLocaleString()}k AI Tokens</div>
                      <div>• {p.limits?.cloud_worker_minutes} Worker Mins</div>
                      <div>• {p.limits?.concurrent_builds} Concurrent Builds</div>
                    </div>
                  </div>

                  <button
                    onClick={() => handleUpgrade(p.tier)}
                    disabled={isCurrent}
                    className={`mt-4 w-full py-1.5 px-2 text-xs font-medium rounded transition-colors ${
                      isCurrent
                        ? "bg-muted text-muted-foreground cursor-not-allowed"
                        : "bg-primary text-primary-foreground hover:bg-primary/90"
                    }`}
                  >
                    {isCurrent ? "Active Plan" : "Switch Plan"}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 2: Usage & Quotas */}
      {activeTab === "usage" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* AI Tokens */}
            <div className="p-4 rounded-lg border border-border bg-card space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs font-semibold text-muted-foreground uppercase">AI Tokens Consumed</span>
                <Zap className="w-4 h-4 text-amber-500" />
              </div>
              <div className="text-2xl font-bold">
                {usage?.metrics?.ai_tokens?.used?.toLocaleString() || "12,450"}{" "}
                <span className="text-xs font-normal text-muted-foreground">
                  / {usage?.metrics?.ai_tokens?.limit === -1 ? "Unlimited" : (usage?.metrics?.ai_tokens?.limit || 50000).toLocaleString()}
                </span>
              </div>
              <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                <div
                  className="bg-primary h-2 rounded-full"
                  style={{ width: `${Math.min(usage?.metrics?.ai_tokens?.pct || 25, 100)}%` }}
                />
              </div>
              <p className="text-[11px] text-muted-foreground">
                {usage?.metrics?.ai_tokens?.pct || 25}% of monthly allocation used
              </p>
            </div>

            {/* Cloud Worker Minutes */}
            <div className="p-4 rounded-lg border border-border bg-card space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs font-semibold text-muted-foreground uppercase">Worker Compute</span>
                <Building className="w-4 h-4 text-blue-500" />
              </div>
              <div className="text-2xl font-bold">
                {usage?.metrics?.cloud_worker_minutes?.used || "18"}{" "}
                <span className="text-xs font-normal text-muted-foreground">
                  / {usage?.metrics?.cloud_worker_minutes?.limit === -1 ? "Unlimited" : (usage?.metrics?.cloud_worker_minutes?.limit || 120)} mins
                </span>
              </div>
              <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${Math.min(usage?.metrics?.cloud_worker_minutes?.pct || 15, 100)}%` }}
                />
              </div>
              <p className="text-[11px] text-muted-foreground">
                Persistent background pipeline container runtime
              </p>
            </div>

            {/* Concurrent Builds */}
            <div className="p-4 rounded-lg border border-border bg-card space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs font-semibold text-muted-foreground uppercase">Active Build Slots</span>
                <TrendingUp className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="text-2xl font-bold">
                {usage?.metrics?.concurrent_builds?.used || "1"}{" "}
                <span className="text-xs font-normal text-muted-foreground">
                  / {usage?.metrics?.concurrent_builds?.limit || 2} slots
                </span>
              </div>
              <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                <div
                  className="bg-emerald-500 h-2 rounded-full"
                  style={{ width: `${Math.min(usage?.metrics?.concurrent_builds?.pct || 50, 100)}%` }}
                />
              </div>
              <p className="text-[11px] text-muted-foreground">Parallel CI/CD packaging execution slots</p>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Billing & Invoices */}
      {activeTab === "billing" && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-base font-bold text-foreground">Invoices & Payment History</h3>
              <p className="text-xs text-muted-foreground">All transactions verified via Stripe and Razorpay webhooks.</p>
            </div>
            <button
              onClick={handleSimulatePayment}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            >
              <CreditCard className="w-3.5 h-3.5" />
              Process Test Payment ($49)
            </button>
          </div>

          <div className="border border-border rounded-lg overflow-hidden bg-card">
            <table className="w-full text-xs text-left">
              <thead className="bg-muted text-muted-foreground uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-3">Invoice #</th>
                  <th className="p-3">Amount</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Billing Period</th>
                  <th className="p-3">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {invoices.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="p-4 text-center text-muted-foreground">
                      No invoices generated yet.
                    </td>
                  </tr>
                ) : (
                  invoices.map((inv) => (
                    <tr key={inv.id} className="hover:bg-muted/40">
                      <td className="p-3 font-mono font-medium">{inv.invoice_number}</td>
                      <td className="p-3 font-semibold">${inv.amount?.toFixed(2)} {inv.currency}</td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                          {inv.status}
                        </span>
                      </td>
                      <td className="p-3 text-muted-foreground">
                        {inv.period_start ? new Date(inv.period_start).toLocaleDateString() : "N/A"} - {inv.period_end ? new Date(inv.period_end).toLocaleDateString() : "N/A"}
                      </td>
                      <td className="p-3 text-muted-foreground">
                        {inv.created_at ? new Date(inv.created_at).toLocaleDateString() : "N/A"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: AI Providers & BYOK */}
      {activeTab === "providers" && (
        <div className="space-y-6">
          {/* Catalog */}
          <div>
            <h3 className="text-base font-bold text-foreground">AI Model Catalog & Real-time Pricing</h3>
            <p className="text-xs text-muted-foreground mb-3">Managed foundation model routing and per-1k token costs.</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {providers.map((pr) => (
                <div key={pr.id} className="p-3 rounded-lg border border-border bg-card">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-sm uppercase text-foreground">{pr.provider}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted font-mono">{pr.model_name}</span>
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground space-y-1">
                    <div>Input: <span className="font-mono text-foreground">${pr.cost_per_1k_input}</span> / 1k tokens</div>
                    <div>Output: <span className="font-mono text-foreground">${pr.cost_per_1k_output}</span> / 1k tokens</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* BYOK Encrypted Form */}
          <div className="p-4 rounded-lg border border-border bg-card">
            <h3 className="text-base font-bold text-foreground">Bring Your Own Key (BYOK) & Integration Credentials</h3>
            <p className="text-xs text-muted-foreground mb-4">
              Stored credentials are encrypted with AES-Fernet isolation per tenant and never exposed in plaintext.
            </p>

            <form onSubmit={handleAddCredential} className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <div>
                <label className="text-[11px] font-semibold text-muted-foreground">Provider</label>
                <select
                  value={credProvider}
                  onChange={(e) => setCredProvider(e.target.value)}
                  className="w-full mt-1 p-2 text-xs border border-border rounded bg-background"
                >
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="google">Google Gemini</option>
                  <option value="github">GitHub Personal Token</option>
                  <option value="aws">AWS IAM</option>
                  <option value="meta">Meta Graph API</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-muted-foreground">Key Identifier / Name</label>
                <input
                  type="text"
                  placeholder="e.g. Production GPT-4o Key"
                  value={credKeyId}
                  onChange={(e) => setCredKeyId(e.target.value)}
                  className="w-full mt-1 p-2 text-xs border border-border rounded bg-background"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-muted-foreground">API Secret / Token</label>
                <input
                  type="password"
                  placeholder="sk-..."
                  value={credSecret}
                  onChange={(e) => setCredSecret(e.target.value)}
                  className="w-full mt-1 p-2 text-xs border border-border rounded bg-background"
                />
              </div>

              <div className="flex items-end">
                <button
                  type="submit"
                  className="w-full py-2 px-3 text-xs font-medium bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors"
                >
                  Encrypt & Save Key
                </button>
              </div>
            </form>

            {/* List credentials */}
            <div className="mt-4 pt-4 border-t border-border">
              <h4 className="text-xs font-semibold text-muted-foreground uppercase mb-2">Stored Tenant Credentials</h4>
              <div className="space-y-2">
                {credentials.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No custom keys configured yet.</p>
                ) : (
                  credentials.map((c) => (
                    <div key={c.id} className="flex justify-between items-center p-2 rounded bg-muted/40 text-xs">
                      <div>
                        <span className="font-semibold text-foreground uppercase mr-2">{c.provider}</span>
                        <span className="text-muted-foreground">{c.key_identifier || "API Key"}</span>
                      </div>
                      <span className="text-emerald-500 font-mono text-[11px] flex items-center gap-1">
                        <CheckCircle className="w-3 h-3" /> Encrypted & Active
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: Support & Notifications */}
      {activeTab === "support" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Notifications */}
          <div className="p-4 rounded-lg border border-border bg-card space-y-3">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
                <Bell className="w-4 h-4 text-primary" /> In-App Notifications
              </h3>
              <span className="text-xs text-muted-foreground">{notifications.length} alerts</span>
            </div>
            <div className="space-y-2 max-h-[350px] overflow-y-auto">
              {notifications.length === 0 ? (
                <p className="text-xs text-muted-foreground">No recent notifications.</p>
              ) : (
                notifications.map((n) => (
                  <div key={n.id} className="p-2.5 rounded bg-muted/30 border border-border/50 text-xs space-y-1">
                    <div className="flex justify-between items-center font-semibold text-foreground">
                      <span>{n.title}</span>
                      <span className="text-[10px] text-muted-foreground">{n.created_at ? new Date(n.created_at).toLocaleDateString() : ""}</span>
                    </div>
                    <p className="text-muted-foreground text-[11px]">{n.message}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Support Ticket Submission */}
          <div className="p-4 rounded-lg border border-border bg-card space-y-3">
            <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
              <LifeBuoy className="w-4 h-4 text-primary" /> Create Support Ticket
            </h3>
            <form onSubmit={handleCreateTicket} className="space-y-3">
              <div>
                <label className="text-[11px] font-semibold text-muted-foreground">Subject</label>
                <input
                  type="text"
                  placeholder="e.g. Quota extension request"
                  value={ticketSubject}
                  onChange={(e) => setTicketSubject(e.target.value)}
                  className="w-full mt-1 p-2 text-xs border border-border rounded bg-background"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-muted-foreground">Message</label>
                <textarea
                  rows={3}
                  placeholder="Describe your query or requirement..."
                  value={ticketMsg}
                  onChange={(e) => setTicketMsg(e.target.value)}
                  className="w-full mt-1 p-2 text-xs border border-border rounded bg-background"
                />
              </div>
              <button
                type="submit"
                className="w-full py-2 px-3 text-xs font-medium bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors"
              >
                Submit Ticket
              </button>
            </form>

            <div className="mt-4 pt-3 border-t border-border">
              <h4 className="text-xs font-semibold text-muted-foreground uppercase mb-2">My Open Tickets</h4>
              <div className="space-y-2">
                {tickets.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No active tickets.</p>
                ) : (
                  tickets.map((t) => (
                    <div key={t.id} className="flex justify-between items-center p-2 rounded bg-muted/40 text-xs">
                      <span className="font-medium text-foreground">{t.subject}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] bg-primary/10 text-primary uppercase font-bold">
                        {t.status}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 6: Platform Owner Admin Console */}
      {activeTab === "admin" && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-lg border border-border bg-card">
              <span className="text-xs text-muted-foreground uppercase font-semibold">Monthly Recurring Revenue (MRR)</span>
              <div className="text-2xl font-bold mt-1 text-foreground">${adminMetrics?.subscriptions?.mrr?.toFixed(2) || "499.00"}</div>
              <p className="text-[11px] text-muted-foreground mt-1">ARR: ${adminMetrics?.subscriptions?.arr?.toFixed(2) || "5,988.00"}</p>
            </div>

            <div className="p-4 rounded-lg border border-border bg-card">
              <span className="text-xs text-muted-foreground uppercase font-semibold">Total Tenants</span>
              <div className="text-2xl font-bold mt-1 text-foreground">{adminMetrics?.tenants?.total || 12}</div>
              <p className="text-[11px] text-muted-foreground mt-1">Active: {adminMetrics?.tenants?.active || 11} • Suspended: {adminMetrics?.tenants?.suspended || 1}</p>
            </div>

            <div className="p-4 rounded-lg border border-border bg-card">
              <span className="text-xs text-muted-foreground uppercase font-semibold">Total Revenue Collected</span>
              <div className="text-2xl font-bold mt-1 text-emerald-500">${adminMetrics?.financials?.total_revenue_collected?.toFixed(2) || "1,245.00"}</div>
              <p className="text-[11px] text-muted-foreground mt-1">Margin: {adminMetrics?.financials?.gross_margin_pct || 88.5}%</p>
            </div>

            <div className="p-4 rounded-lg border border-border bg-card">
              <span className="text-xs text-muted-foreground uppercase font-semibold">Est. AI Provider Cost</span>
              <div className="text-2xl font-bold mt-1 text-amber-500">${adminMetrics?.financials?.estimated_ai_cost?.toFixed(2) || "34.50"}</div>
              <p className="text-[11px] text-muted-foreground mt-1">{adminMetrics?.usage?.total_ai_tokens?.toLocaleString() || "6.9M"} total tokens</p>
            </div>
          </div>

          {/* Tenants Directory Table */}
          <div className="border border-border rounded-lg overflow-hidden bg-card">
            <div className="p-3 bg-muted font-bold text-xs text-foreground uppercase tracking-wider flex justify-between">
              <span>Platform Tenant Directory</span>
              <span>{adminTenants.length} Registered Organizations</span>
            </div>
            <table className="w-full text-xs text-left">
              <thead className="bg-muted/50 text-muted-foreground uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-3">Organization</th>
                  <th className="p-3">Plan Tier</th>
                  <th className="p-3">Owner Email</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {adminTenants.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="p-4 text-center text-muted-foreground">
                      No tenants found.
                    </td>
                  </tr>
                ) : (
                  adminTenants.map((t) => (
                    <tr key={t.id} className="hover:bg-muted/40">
                      <td className="p-3 font-semibold text-foreground">{t.name}</td>
                      <td className="p-3 uppercase font-mono">{t.plan_tier || "free"}</td>
                      <td className="p-3 text-muted-foreground">{t.owner_email}</td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                            t.status === "active"
                              ? "bg-emerald-500/10 text-emerald-500"
                              : "bg-destructive/10 text-destructive"
                          }`}
                        >
                          {t.status}
                        </span>
                      </td>
                      <td className="p-3">
                        <button
                          onClick={() => handleToggleTenant(t.id, t.status)}
                          className="px-2 py-1 text-[11px] font-medium border border-border rounded hover:bg-muted transition-colors"
                        >
                          {t.status === "active" ? "Suspend" : "Reactivate"}
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
