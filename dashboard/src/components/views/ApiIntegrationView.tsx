"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Network, CheckCircle2, AlertCircle, CreditCard, Mail, MessageSquare, MapPin } from "lucide-react";
import { fetchIntegrations } from "@/lib/api";

export function ApiIntegrationView() {
  const { data: integrations, isLoading } = useQuery({
    queryKey: ["integrations-list"],
    queryFn: fetchIntegrations,
  });

  const supported = [
    { name: "Stripe Payment Gateway", type: "Billing & Subscriptions", icon: CreditCard, status: "Active" },
    { name: "Razorpay Checkout", type: "UPI & Netbanking", icon: CreditCard, status: "Configured" },
    { name: "SendGrid Email API", type: "Transactional Notifications", icon: Mail, status: "Active" },
    { name: "Twilio SMS Service", type: "OTP Verification", icon: MessageSquare, status: "Configured" },
    { name: "Google Maps Platform", type: "Geocoding & Places", icon: MapPin, status: "Ready" },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Network className="w-5 h-5 text-indigo-400" />
          Third-Party Enterprise API Connectors
        </h3>
        <p className="text-xs text-slate-400 mt-1">
          Secure outbound HTTP connectors, payment gateways, and notification service providers.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {supported.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div key={idx} className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                  <Icon className="w-5 h-5" />
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
  );
}
