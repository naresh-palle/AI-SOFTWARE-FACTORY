"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Network,
  CheckCircle2,
  AlertCircle,
  CreditCard,
  Mail,
  MessageSquare,
  MapPin,
  Share2,
  Camera,
  Users,
  Hash,
  Video,
  ExternalLink,
  ShieldCheck,
  RefreshCw,
  Key,
  Layers,
  Activity,
  Send,
} from "lucide-react";
import {
  fetchIntegrations,
  fetchSocialConnections,
  fetchSocialLogs,
  fetchXPricing,
  initiateSocialOAuth,
} from "@/lib/api";

export function ApiIntegrationView() {
  const queryClient = useQueryClient();
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
  const [oauthDialog, setOauthDialog] = useState<{
    platform: string;
    authUrl: string;
    state: string;
  } | null>(null);

  const { data: enterpriseIntegrations } = useQuery({
    queryKey: ["integrations-list"],
    queryFn: fetchIntegrations,
  });

  const { data: socialConnections, isLoading: connectionsLoading, refetch: refetchConnections } = useQuery({
    queryKey: ["social-connections"],
    queryFn: () => fetchSocialConnections(),
  });

  const { data: socialLogs, isLoading: logsLoading } = useQuery({
    queryKey: ["social-logs-all"],
    queryFn: () => fetchSocialLogs(20),
  });

  const { data: xPricing } = useQuery({
    queryKey: ["x-pricing"],
    queryFn: fetchXPricing,
  });

  const oauthMutation = useMutation({
    mutationFn: (platform: string) => initiateSocialOAuth(platform),
    onSuccess: (data) => {
      setOauthDialog({
        platform: data.platform,
        authUrl: data.authorization_url,
        state: data.state,
      });
    },
  });

  const handleStartOAuth = (platformKey: string) => {
    setSelectedPlatform(platformKey);
    oauthMutation.mutate(platformKey);
  };

  const enterpriseSupported = [
    { name: "Stripe Payment Gateway", type: "Billing & Subscriptions", icon: CreditCard, status: "Active" },
    { name: "Razorpay Checkout", type: "UPI & Netbanking", icon: CreditCard, status: "Configured" },
    { name: "SendGrid Email API", type: "Transactional Notifications", icon: Mail, status: "Active" },
    { name: "Twilio SMS Service", type: "OTP Verification", icon: MessageSquare, status: "Configured" },
    { name: "Google Maps Platform", type: "Geocoding & Places", icon: MapPin, status: "Ready" },
  ];

  const socialPlatforms = [
    {
      id: "facebook",
      name: "Facebook Pages & Feed",
      category: "Meta Ecosystem",
      icon: Camera,
      authType: "OAuth 2.0 (User & Page Tokens)",
      features: ["Page feed publishing", "Page insights", "Permissions tracking"],
      color: "text-blue-400 bg-blue-500/10 border-blue-500/20",
    },
    {
      id: "instagram",
      name: "Instagram Graph API",
      category: "Meta Ecosystem",
      icon: Camera,
      authType: "OAuth 2.0 (IG Business)",
      features: ["Container media publishing", "Audience insights", "Reels metadata"],
      color: "text-pink-400 bg-pink-500/10 border-pink-500/20",
    },
    {
      id: "whatsapp",
      name: "WhatsApp Cloud Platform",
      category: "Meta Ecosystem",
      icon: MessageSquare,
      authType: "System User Token (WABA)",
      features: ["Template notifications", "Customer opt-in enforcement", "Inbound webhooks"],
      color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    },
    {
      id: "messenger",
      name: "Messenger API",
      category: "Meta Ecosystem",
      icon: MessageSquare,
      authType: "OAuth 2.0 (Page Scopes)",
      features: ["Conversational messaging", "Interactive buttons", "Messaging webhooks"],
      color: "text-sky-400 bg-sky-500/10 border-sky-500/20",
    },
    {
      id: "threads",
      name: "Threads API",
      category: "Meta Ecosystem",
      icon: Camera,
      authType: "OAuth 2.0 (Threads Scopes)",
      features: ["Two-step thread creation", "User profile query", "Post metrics"],
      color: "text-purple-400 bg-purple-500/10 border-purple-500/20",
    },
    {
      id: "youtube",
      name: "YouTube Data API v3",
      category: "Google Cloud",
      icon: Video,
      authType: "Google OAuth 2.0",
      features: ["Channel audit", "Video metadata", "10,000 unit/day quota tracker"],
      color: "text-red-400 bg-red-500/10 border-red-500/20",
    },
    {
      id: "x",
      name: "X (Twitter) API v2",
      category: "Social Feed & Trends",
      icon: Hash,
      authType: "OAuth 2.0 PKCE",
      features: ["Tweet posting", "Tier quota monitoring (Free/Basic/Pro)", "CRC Webhook"],
      color: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
    },
    {
      id: "linkedin",
      name: "LinkedIn Share API",
      category: "Professional Network",
      icon: Users,
      authType: "OAuth 2.0 (OpenID Connect)",
      features: ["User profile query", "Organization share posts", "Rich media UGC"],
      color: "text-blue-500 bg-blue-600/10 border-blue-600/20",
    },
    {
      id: "tiktok",
      name: "TikTok Creator Platform",
      category: "Short-Form Video",
      icon: Video,
      authType: "OAuth 2.0 (TikTok Login Kit)",
      features: ["User info retrieval", "Video catalog query", "Post publishing"],
      color: "text-teal-400 bg-teal-500/10 border-teal-500/20",
    },
  ];

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Network className="w-5 h-5 text-indigo-400" />
            API & Social Platform Integrations Hub
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Unified integration gateway connecting 5 enterprise third-party APIs and 9 social platform developer engines.
          </p>
        </div>
        <div className="text-right">
          <span className="text-[10px] text-slate-500 font-mono">Security Standard</span>
          <p className="text-xs font-bold text-emerald-400 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" /> Fernet AES-256 + PKCE
          </p>
        </div>
      </div>

      {/* OAuth Initiation Modal */}
      {oauthDialog && (
        <div className="p-4 rounded-xl border border-indigo-800/80 bg-indigo-950/40 text-xs space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="font-bold text-white flex items-center gap-2">
              <Key className="w-4 h-4 text-indigo-400" />
              PKCE OAuth Authorization Flow Initiated ({oauthDialog.platform.toUpperCase()})
            </h4>
            <button
              onClick={() => setOauthDialog(null)}
              className="text-slate-400 hover:text-white text-xs px-2 py-0.5"
            >
              Close
            </button>
          </div>
          <div className="bg-slate-950 p-3 rounded border border-slate-800 font-mono text-[11px] break-all">
            <span className="text-[10px] uppercase text-slate-500 block">Signed State: {oauthDialog.state}</span>
            <span className="text-indigo-300 block mt-1">Authorization URL:</span>
            <p className="text-slate-300 mt-0.5">{oauthDialog.authUrl}</p>
          </div>
          <div className="flex justify-end gap-2">
            <a
              href={oauthDialog.authUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              Open Authorization Link <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      )}

      {/* Social Platform Developer Engines (9 Platforms) */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <Share2 className="w-4 h-4 text-cyan-400" />
              Social Platform Developer Automation Connectors (9 Platforms)
            </h4>
            <p className="text-xs text-slate-400 mt-0.5">
              Full OAuth PKCE lifecycle, multi-tenant token isolation, and automated publishing APIs.
            </p>
          </div>
          <button
            onClick={() => refetchConnections()}
            className="text-xs font-mono text-slate-400 hover:text-white flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800/60 border border-slate-700/60"
          >
            <RefreshCw className="w-3 h-3" /> Refresh Connections
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {socialPlatforms.map((p) => {
            const Icon = p.icon;
            const isConnecting = oauthMutation.isPending && selectedPlatform === p.id;
            return (
              <div
                key={p.id}
                className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-3 flex flex-col justify-between hover:border-slate-700 transition-colors"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <div className={`p-2 rounded-lg border ${p.color}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-2 py-0.5 rounded">
                      Engine Active
                    </span>
                  </div>
                  <h4 className="text-xs font-bold text-white mt-2.5">{p.name}</h4>
                  <p className="text-[10px] text-slate-400 font-mono">{p.category} • {p.authType}</p>
                  <ul className="mt-2 space-y-1">
                    {p.features.map((feat, i) => (
                      <li key={i} className="text-[11px] text-slate-300 flex items-center gap-1.5">
                        <span className="w-1 h-1 rounded-full bg-slate-500" />
                        {feat}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
                  <span className="text-[10px] font-mono text-slate-500">v2 / v19.0 REST</span>
                  <button
                    onClick={() => handleStartOAuth(p.id)}
                    disabled={isConnecting}
                    className="text-[11px] px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white font-medium flex items-center gap-1 transition-colors"
                  >
                    <Key className="w-3 h-3 text-cyan-400" />
                    {isConnecting ? "Generating..." : "Initiate OAuth"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Active OAuth Connections Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800 flex items-center justify-between">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Key className="w-4 h-4 text-emerald-400" />
            Active Platform OAuth Connections & Scopes
          </h4>
          <span className="text-[10px] text-slate-500 font-mono">Tenant: factory_default</span>
        </div>
        {!socialConnections || socialConnections.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-500 font-mono">
            No active customer or factory OAuth connections configured yet. Use &ldquo;Initiate OAuth&rdquo; above to link accounts.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/50 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="p-3">Platform</th>
                  <th className="p-3">Account Type</th>
                  <th className="p-3">Account Identifier</th>
                  <th className="p-3">Granted Scopes</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Rate Headroom</th>
                  <th className="p-3">Last Refreshed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 font-mono text-[11px]">
                {socialConnections.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/20">
                    <td className="p-3 font-semibold text-white uppercase">{c.platform}</td>
                    <td className="p-3 text-slate-300">{c.account_type || "customer"}</td>
                    <td className="p-3 text-slate-300">{c.account_name || c.id.slice(0, 8) + "..."}</td>
                    <td className="p-3 text-cyan-400">{c.scopes ? `${c.scopes.length} scopes` : "Standard"}</td>
                    <td className="p-3">
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-950/60 text-emerald-400 border border-emerald-800/40">
                        {c.status}
                      </span>
                    </td>
                    <td className="p-3 text-slate-400">{c.rate_limit_remaining ?? "Dynamic"}</td>
                    <td className="p-3 text-slate-500 text-[10px]">
                      {c.last_refreshed_at ? new Date(c.last_refreshed_at).toLocaleString() : "Active"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* X API Pricing & Tier Explorer */}
      {xPricing && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Hash className="w-4 h-4 text-cyan-400" />
                X (Twitter) Developer API v2 Pricing & Rate Limits
              </h4>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Quota limits strictly enforced in `XApiAgent` to prevent billing overruns.
              </p>
            </div>
            <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800/40 px-2 py-0.5 rounded">
              Tier Quota Tracker Active
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(xPricing).map(([tierKey, tier]: [string, any]) => (
              <div key={tierKey} className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white uppercase font-mono">{tierKey} Tier</span>
                  <span className="text-xs font-mono font-bold text-emerald-400">
                    ${tier.monthly_cost_usd}/mo
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">{tier.description}</p>
                <div className="pt-2 text-[10px] font-mono text-slate-300 space-y-1 border-t border-slate-800/60">
                  <div>Reads: {tier.read_limit_monthly.toLocaleString()} / month</div>
                  <div>Writes: {tier.write_limit_monthly.toLocaleString()} / month</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Enterprise Third-Party Connectors */}
      <div className="space-y-4">
        <div>
          <h4 className="text-sm font-bold text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            Standard Enterprise Third-Party Connectors
          </h4>
          <p className="text-xs text-slate-400 mt-0.5">
            Payment processors, transactional mail, and SMS gatekeepers.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {enterpriseSupported.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-2 py-0.5 rounded">
                    {item.status}
                  </span>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">{item.name}</h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">{item.type}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
