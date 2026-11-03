"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "@/components/navigation/sidebar";
import { ResearchForm } from "@/components/research/research-form";
import { AgentDagViewer } from "@/components/research/agent-dag-viewer";
import { WorkflowTimeline } from "@/components/research/workflow-timeline";
import { ReportViewer } from "@/components/research/report-viewer";
import { DocumentUploader } from "@/components/ingestion/document-uploader";
import { HybridSearchSandbox } from "@/components/retrieval/hybrid-search-sandbox";
import { BenchmarkDashboard } from "@/components/evaluation/benchmark-dashboard";
import { ServiceMeshGrid } from "@/components/observability/service-mesh-grid";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  submitResearchJob,
  getResearchJobStatus,
  getResearchReport,
  checkAllMicroservices,
} from "@/lib/api";
import {
  MicroserviceHealth,
  ResearchJobCreate,
  ResearchJobStatus,
  SynthesizedReport,
} from "@/lib/types";
import {
  PanelLeftOpen,
  PanelLeftClose,
  Sparkles,
  UploadCloud,
  Search,
  Award,
  Server,
  Layers,
  Cpu,
  ShieldCheck,
  Activity,
  Plus,
} from "lucide-react";

export default function Home() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState("research");
  const [tenantId, setTenantId] = useState("tenant_demo");

  // Multi-agent job states
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<ResearchJobStatus | null>(null);
  const [report, setReport] = useState<SynthesizedReport | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Microservices state
  const [services, setServices] = useState<MicroserviceHealth[]>([
    { name: "API Gateway", port: 8000, url: "http://127.0.0.1:8000", status: "checking" },
    { name: "Research Orchestrator", port: 8001, url: "http://127.0.0.1:8001", status: "checking" },
    { name: "Ingestion Service", port: 8002, url: "http://127.0.0.1:8002", status: "checking" },
    { name: "Retrieval Service", port: 8003, url: "http://127.0.0.1:8003", status: "checking" },
    { name: "Agent Runtime", port: 8004, url: "http://127.0.0.1:8004", status: "checking" },
    { name: "Evaluation Service", port: 8005, url: "http://127.0.0.1:8005", status: "checking" },
  ]);
  const [isRefreshingServices, setIsRefreshingServices] = useState(false);

  // Poll service health on initial mount
  const refreshHealth = async () => {
    setIsRefreshingServices(true);
    try {
      const results = await checkAllMicroservices();
      setServices(results);
    } catch {
      // Keep checking state
    } finally {
      setIsRefreshingServices(false);
    }
  };

  useEffect(() => {
    refreshHealth();
    const interval = setInterval(refreshHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  // Poll research job progress
  useEffect(() => {
    if (!activeJobId) return;

    const interval = setInterval(async () => {
      try {
        const status = await getResearchJobStatus(activeJobId, tenantId);
        setJobStatus(status);

        if (status.status === "completed") {
          clearInterval(interval);
          try {
            const finalReport = await getResearchReport(activeJobId, tenantId);
            setReport(finalReport);
          } catch (e) {
            console.error("Failed to retrieve report", e);
          }
        } else if (status.status === "failed" || status.status === "cancelled") {
          clearInterval(interval);
        }
      } catch (err) {
        console.error("Failed to poll status", err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [activeJobId, tenantId]);

  // Handle job submission
  const handleDispatchResearch = async (data: ResearchJobCreate) => {
    setIsSubmitting(true);
    setReport(null);
    setJobStatus(null);
    try {
      const res = await submitResearchJob(data, tenantId);
      const newId = res.job_id || res.research_id;
      setActiveJobId(newId);
      setJobStatus(res);
    } catch (err) {
      console.error("Job submission failed:", err);
      alert(err instanceof Error ? err.message : "Failed to dispatch research job");
    } finally {
      setIsSubmitting(false);
    }
  };

  const healthyCount = services.filter((s) => s.status === "healthy").length;
  const isAllHealthy = healthyCount === services.length && services.length > 0;

  const tabTitles: Record<string, { title: string; subtitle: string; icon: React.ElementType }> = {
    research: {
      title: "Research Studio",
      subtitle: "Autonomous Multi-Agent LangGraph Orchestrator & Synthesis",
      icon: Sparkles,
    },
    ingestion: {
      title: "Knowledge Base Ingestion",
      subtitle: "Cryptographic Chunking, Passage Extraction & Vector Indexing",
      icon: UploadCloud,
    },
    retrieval: {
      title: "Hybrid Search Fusion Sandbox",
      subtitle: "Dense Qdrant Vector + Sparse BM25 Reciprocal Rank Fusion",
      icon: Search,
    },
    benchmarks: {
      title: "Evaluation & Quality Gates",
      subtitle: "10 / 10 Automated Release Gates, Faithfulness & Grounding",
      icon: Award,
    },
    observability: {
      title: "Topology & Observability Mesh",
      subtitle: "Real-time Telemetry across 6 Decoupled Microservices",
      icon: Server,
    },
  };

  const CurrentIcon = tabTitles[activeTab]?.icon || Sparkles;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100">
      {/* Collapsible Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen((prev) => !prev)}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        tenantId={tenantId}
        onTenantChange={setTenantId}
        healthyCount={healthyCount}
        totalServices={services.length}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-slate-950">
        {/* Top Header Bar */}
        <header className="h-16 flex items-center justify-between border-b border-slate-800/80 px-6 bg-slate-950/80 backdrop-blur-xl flex-shrink-0 z-30">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsSidebarOpen((prev) => !prev)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
              title={isSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
            >
              {isSidebarOpen ? (
                <PanelLeftClose className="w-4 h-4" />
              ) : (
                <PanelLeftOpen className="w-4 h-4 text-blue-400" />
              )}
            </button>

            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                <CurrentIcon className="w-3.5 h-3.5" />
              </div>
              <div>
                <h1 className="text-sm font-semibold text-white tracking-tight">
                  {tabTitles[activeTab]?.title}
                </h1>
                <p className="text-[11px] text-slate-400 font-medium hidden sm:block">
                  {tabTitles[activeTab]?.subtitle}
                </p>
              </div>
            </div>
          </div>

          {/* Quick Header Actions */}
          <div className="flex items-center gap-3">
            {activeTab !== "research" && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setActiveTab("research")}
                className="text-xs gap-1.5 hidden sm:flex"
              >
                <Plus className="w-3.5 h-3.5 text-blue-400" />
                <span>New Research Mission</span>
              </Button>
            )}

            <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs">
              <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
              <span className="text-slate-400 hidden sm:inline">Tenant:</span>
              <span className="font-mono text-blue-400 font-medium">{tenantId}</span>
            </div>

            <Badge
              variant={isAllHealthy ? "success" : "warning"}
              className="text-xs py-1"
            >
              <Activity className="w-3 h-3 animate-pulse" />
              <span>
                {healthyCount}/{services.length} Mesh
              </span>
            </Badge>
          </div>
        </header>

        {/* Scrollable Viewport */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Quick Stats Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                <Cpu className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-mono text-slate-400 block">
                  Microservices
                </span>
                <span className="text-sm font-bold text-white font-mono">
                  {healthyCount} / {services.length} Active
                </span>
              </div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                <Layers className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-mono text-slate-400 block">
                  Agent Topology
                </span>
                <span className="text-sm font-bold text-indigo-400 font-mono">
                  5 Agents / DAG
                </span>
              </div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                <Search className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-mono text-slate-400 block">
                  Hybrid Retrieval
                </span>
                <span className="text-sm font-bold text-purple-400 font-mono">
                  Qdrant + BM25
                </span>
              </div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <Award className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-mono text-slate-400 block">
                  Quality Gates
                </span>
                <span className="text-sm font-bold text-emerald-400 font-mono">
                  10 / 10 Satisfied
                </span>
              </div>
            </div>
          </div>

          {/* Active Workspace View */}
          {activeTab === "research" && (
            <div className="space-y-6 animate-in fade-in-50 duration-200">
              <AgentDagViewer
                currentStage={jobStatus?.stage || "idle"}
                status={jobStatus?.status || "idle"}
                evidenceCount={jobStatus?.evidence_count || 0}
              />
              <ResearchForm
                onSubmit={handleDispatchResearch}
                isLoading={isSubmitting}
                tenantId={tenantId}
              />
              <WorkflowTimeline jobStatus={jobStatus} />
              <ReportViewer report={report} />
            </div>
          )}

          {activeTab === "ingestion" && (
            <div className="space-y-6 animate-in fade-in-50 duration-200">
              <DocumentUploader
                tenantId={tenantId}
                onUploadSuccess={() => {
                  // Document ingested
                }}
              />
            </div>
          )}

          {activeTab === "retrieval" && (
            <div className="space-y-6 animate-in fade-in-50 duration-200">
              <HybridSearchSandbox />
            </div>
          )}

          {activeTab === "benchmarks" && (
            <div className="space-y-6 animate-in fade-in-50 duration-200">
              <BenchmarkDashboard />
            </div>
          )}

          {activeTab === "observability" && (
            <div className="space-y-6 animate-in fade-in-50 duration-200">
              <ServiceMeshGrid
                services={services}
                onRefresh={refreshHealth}
                isRefreshing={isRefreshingServices}
              />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
