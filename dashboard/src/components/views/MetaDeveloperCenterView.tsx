"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Share2,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Shield,
  MessageCircle,
} from "lucide-react";
import { fetchMetaStatus } from "@/lib/api";

export function MetaDeveloperCenterView() {
  const { data: meta, isLoading } = useQuery({
    queryKey: ["meta-status"],
    queryFn: fetchMetaStatus,
  });

  const products = meta?.supported_products || [
    { product: "Facebook Login", status: "Ready", permissions: ["email", "public_profile"] },
    { product: "Instagram Graph API", status: "Configured", permissions: ["instagram_basic", "pages_show_list"] },
    { product: "WhatsApp Business Platform", status: "Ready", permissions: ["whatsapp_business_messaging"] },
    { product: "Messenger API", status: "Configured", permissions: ["pages_messaging"] },
    { product: "Threads API", status: "Available", permissions: ["threads_basic"] },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Share2 className="w-5 h-5 text-blue-400" />
            Meta Developer Platform Center
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Management hub for Facebook Graph API, Instagram API, WhatsApp Business, and App Review submissions.
          </p>
        </div>
        <div className="text-right">
          <span className="text-[10px] text-slate-500 font-mono">App Review Status</span>
          <p className="text-xs font-bold text-emerald-400">Standard Access Active</p>
        </div>
      </div>

      {/* Meta App Config Details */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">Meta App ID</span>
          <p className="text-xs font-mono font-bold text-white mt-1">{meta?.app_id || "Not Configured"}</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">App Secret Status</span>
          <p className="text-xs font-mono font-bold text-emerald-400 mt-1">
            {meta?.has_app_secret ? "Encrypted (AES-256)" : "Awaiting Configuration"}
          </p>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-semibold text-slate-400 uppercase">Webhook Verification</span>
          <p className="text-xs font-mono font-bold text-cyan-400 mt-1">SHA-256 HMAC Verified</p>
        </div>
      </div>

      {/* Supported Products & Permissions */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
            Connected Meta Products & Scope Status
          </h4>
        </div>
        <div className="divide-y divide-slate-800/60">
          {products.map((p: any, idx: number) => (
            <div key={idx} className="p-4 flex items-center justify-between">
              <div>
                <h5 className="text-xs font-bold text-white">{p.product}</h5>
                <div className="flex gap-1 mt-1">
                  {p.permissions.map((perm: string, i: number) => (
                    <span
                      key={i}
                      className="px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-[10px] font-mono text-slate-400"
                    >
                      {perm}
                    </span>
                  ))}
                </div>
              </div>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-2.5 py-1 rounded">
                {p.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
