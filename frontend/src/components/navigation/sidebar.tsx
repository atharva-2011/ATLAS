"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  Sparkles,
  UploadCloud,
  Search,
  Award,
  Server,
  PanelLeftClose,
  PanelLeftOpen,
  ShieldCheck,
  Activity,
  ExternalLink,
} from "lucide-react";

export interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
  description: string;
  badge?: string;
  badgeVariant?: "default" | "success" | "warning" | "cyan";
}

export const NAV_ITEMS: NavItem[] = [
  {
    id: "research",
    label: "Research Studio",
    icon: Sparkles,
    description: "Multi-Agent LangGraph Orchestrator",
    badge: "Active",
    badgeVariant: "cyan",
  },
  {
    id: "ingestion",
    label: "Knowledge Base",
    icon: UploadCloud,
    description: "Document Chunking & Hashes",
    badge: "Dual Index",
    badgeVariant: "default",
  },
  {
    id: "retrieval",
    label: "Hybrid Search",
    icon: Search,
    description: "Vector Dense + BM25 RRF Fusion",
    badge: "k=60",
    badgeVariant: "default",
  },
  {
    id: "benchmarks",
    label: "Evaluation Gates",
    icon: Award,
    description: "NLI Grounding & RAG Triad",
    badge: "10/10",
    badgeVariant: "success",
  },
  {
    id: "observability",
    label: "Topology Mesh",
    icon: Server,
    description: "6 Microservices Telemetry",
    badge: ":8000-8005",
    badgeVariant: "default",
  },
];

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  activeTab: string;
  onTabChange: (tabId: string) => void;
  tenantId: string;
  onTenantChange: (t: string) => void;
  healthyCount: number;
  totalServices: number;
}

export function Sidebar({
  isOpen,
  onToggle,
  activeTab,
  onTabChange,
  tenantId,
  onTenantChange,
  healthyCount,
  totalServices,
}: SidebarProps) {
  const isAllHealthy = healthyCount === totalServices && totalServices > 0;

  return (
    <aside
      className={cn(
        "relative flex flex-col justify-between border-r border-slate-800/80 bg-slate-950/95 backdrop-blur-2xl transition-all duration-300 ease-in-out z-40 select-none",
        isOpen ? "w-64" : "w-16 sm:w-20"
      )}
    >
      {/* Top Header & Brand */}
      <div>
        <div
          className={cn(
            "h-16 flex items-center border-b border-slate-800/80 px-3.5",
            isOpen ? "justify-between" : "justify-center"
          )}
        >
          {/* Logo & Name */}
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="relative flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-cyan-400 p-0.5 shadow-lg shadow-blue-500/20">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-blue-400 animate-pulse" />
              </div>
              <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500" />
              </span>
            </div>

            {isOpen && (
              <div className="flex flex-col animate-in fade-in-50 duration-200">
                <div className="flex items-center gap-1.5">
                  <span className="text-base font-bold tracking-tight text-white">
                    ATLAS
                  </span>
                  <Badge variant="cyan" className="text-[9px] py-0 px-1 font-mono">
                    v2.0
                  </Badge>
                </div>
                <span className="text-[10px] text-slate-400 font-medium truncate">
                  Research Mesh
                </span>
              </div>
            )}
          </div>

          {/* Toggle Button */}
          {isOpen && (
            <button
              onClick={onToggle}
              title="Collapse sidebar to icon rail"
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors cursor-pointer"
            >
              <PanelLeftClose className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Collapsed Toggle Button (when closed) */}
        {!isOpen && (
          <div className="flex justify-center py-2.5 border-b border-slate-800/40">
            <button
              onClick={onToggle}
              title="Expand sidebar"
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors cursor-pointer"
            >
              <PanelLeftOpen className="w-4 h-4 text-blue-400" />
            </button>
          </div>
        )}

        {/* Navigation Items */}
        <nav className="p-2 space-y-1 mt-2">
          {NAV_ITEMS.map((item) => {
            const isActive = activeTab === item.id;
            const Icon = item.icon;

            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                title={!isOpen ? item.label : undefined}
                className={cn(
                  "w-full flex items-center rounded-xl transition-all duration-200 cursor-pointer relative group",
                  isOpen
                    ? "px-3 py-2.5 gap-3 justify-start"
                    : "p-2.5 justify-center",
                  isActive
                    ? "bg-gradient-to-r from-blue-600/20 via-indigo-600/15 to-transparent text-white border border-blue-500/30 shadow-md shadow-blue-500/5"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                )}
              >
                {/* Active Indicator Bar */}
                {isActive && (
                  <span className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r-full bg-blue-500" />
                )}

                <div
                  className={cn(
                    "flex items-center justify-center rounded-lg transition-transform group-hover:scale-105",
                    isActive
                      ? "text-blue-400"
                      : "text-slate-400 group-hover:text-slate-200"
                  )}
                >
                  <Icon className={cn("w-5 h-5 flex-shrink-0")} />
                </div>

                {isOpen && (
                  <div className="flex-1 flex items-center justify-between overflow-hidden text-left animate-in fade-in-50 duration-150">
                    <div className="truncate">
                      <span className="text-xs font-semibold block text-slate-200">
                        {item.label}
                      </span>
                      <span className="text-[10px] text-slate-400 truncate block">
                        {item.description}
                      </span>
                    </div>

                    {item.badge && (
                      <Badge
                        variant={item.badgeVariant || "default"}
                        className="text-[9px] py-0 px-1 font-mono flex-shrink-0"
                      >
                        {item.badge}
                      </Badge>
                    )}
                  </div>
                )}

                {/* Floating Tooltip when Collapsed */}
                {!isOpen && (
                  <div className="absolute left-full ml-3 px-2.5 py-1.5 bg-slate-900 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 shadow-xl opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition-opacity z-50 whitespace-nowrap">
                    <p className="font-semibold text-white">{item.label}</p>
                    <p className="text-[10px] text-slate-400">{item.description}</p>
                  </div>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Footer Section: Tenant & Mesh Status */}
      <div className="p-3 border-t border-slate-800/80 space-y-3 bg-slate-950/60">
        {isOpen ? (
          <div className="space-y-3 animate-in fade-in-50 duration-200">
            {/* Tenant Selector */}
            <div className="bg-slate-900 border border-slate-800/80 rounded-xl p-2.5">
              <div className="flex items-center justify-between mb-1.5 text-[11px] text-slate-400">
                <span className="flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
                  <span>Tenant Isolation</span>
                </span>
                <span className="text-[9px] font-mono text-emerald-400">RLS Active</span>
              </div>
              <select
                value={tenantId}
                onChange={(e) => onTenantChange(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-xs text-slate-200 font-medium focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
              >
                <option value="tenant_demo">tenant_demo</option>
                <option value="tenant_alpha">tenant_alpha</option>
                <option value="default">default</option>
              </select>
            </div>

            {/* Service Mesh Status */}
            <div className="bg-slate-900 border border-slate-800/80 rounded-xl p-2.5 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity
                  className={cn(
                    "w-4 h-4",
                    isAllHealthy ? "text-emerald-400 animate-pulse" : "text-amber-400"
                  )}
                />
                <span className="text-xs text-slate-300 font-medium">Service Mesh</span>
              </div>
              <Badge
                variant={isAllHealthy ? "success" : "warning"}
                className="text-[10px] py-0 px-1.5 font-mono"
              >
                {healthyCount}/{totalServices}
              </Badge>
            </div>

            {/* Quick Links */}
            <div className="flex items-center justify-between text-[11px] text-slate-400 px-1 pt-1">
              <span>ATLAS Core v2.0</span>
              <a
                href="https://github.com/atharva-2011/ATLAS"
                target="_blank"
                rel="noreferrer"
                className="hover:text-white flex items-center gap-1 transition-colors"
              >
                <span>GitHub</span>
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
            </div>
          </div>
        ) : (
          /* Collapsed Bottom Icons */
          <div className="flex flex-col items-center space-y-2 py-1">
            {/* Mesh Pulsing Dot */}
            <div
              title={`Service Mesh: ${healthyCount}/${totalServices} Active`}
              className="relative cursor-pointer p-1.5 rounded-lg hover:bg-slate-900"
              onClick={() => onTabChange("observability")}
            >
              <Activity
                className={cn(
                  "w-4 h-4",
                  isAllHealthy ? "text-emerald-400" : "text-amber-400"
                )}
              />
              <span
                className={cn(
                  "absolute top-1 right-1 w-2 h-2 rounded-full",
                  isAllHealthy ? "bg-emerald-500 animate-ping" : "bg-amber-500"
                )}
              />
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}

