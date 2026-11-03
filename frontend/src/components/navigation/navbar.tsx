"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import {
  Activity,
  ShieldCheck,
  Sparkles,
  ExternalLink,
} from "lucide-react";

interface NavbarProps {
  tenantId: string;
  onTenantChange: (t: string) => void;
  healthyCount: number;
  totalServices: number;
}

export function Navbar({
  tenantId,
  onTenantChange,
  healthyCount,
  totalServices,
}: NavbarProps) {
  const isAllHealthy = healthyCount === totalServices && totalServices > 0;

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-cyan-400 p-0.5 shadow-lg shadow-blue-500/20">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-blue-400 animate-pulse" />
            </div>
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500" />
            </span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                ATLAS
              </span>
              <Badge variant="cyan" className="text-[10px] py-0 px-1.5 font-mono">
                v2.0
              </Badge>
            </div>
            <p className="text-[11px] text-slate-400 font-medium hidden sm:block">
              Autonomous Multi-Agent Scientific Research & Verification Mesh
            </p>
          </div>
        </div>

        {/* Right Navigation & Status */}
        <div className="flex items-center gap-3 sm:gap-4">
          {/* Tenant Selector */}
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1">
            <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-xs text-slate-400 hidden sm:inline">Tenant:</span>
            <select
              value={tenantId}
              onChange={(e) => onTenantChange(e.target.value)}
              className="bg-transparent text-xs text-slate-200 font-medium focus:outline-none cursor-pointer"
            >
              <option value="tenant_demo" className="bg-slate-900 text-slate-200">
                tenant_demo
              </option>
              <option value="tenant_alpha" className="bg-slate-900 text-slate-200">
                tenant_alpha
              </option>
              <option value="default" className="bg-slate-900 text-slate-200">
                default
              </option>
            </select>
          </div>

          {/* Service Mesh Status */}
          <div className="flex items-center gap-2">
            <Badge
              variant={isAllHealthy ? "success" : "warning"}
              className="text-xs py-1"
            >
              <Activity className="w-3 h-3 animate-pulse" />
              <span>
                {healthyCount}/{totalServices} Mesh Active
              </span>
            </Badge>
          </div>

          {/* Direct Docs / GitHub */}
          <a
            href="https://github.com/atharva-2011/ATLAS"
            target="_blank"
            rel="noreferrer"
            className="text-xs text-slate-400 hover:text-white transition-colors flex items-center gap-1 hidden md:flex"
          >
            <span>GitHub</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>
    </header>
  );
}

