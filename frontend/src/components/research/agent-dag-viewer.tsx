"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Brain,
  Search,
  FileText,
  ShieldAlert,
  Sparkles,
  Loader2,
  ArrowRight,
  GitFork,
  Check,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface AgentNode {
  id: string;
  name: string;
  role: string;
  icon: React.ElementType;
  description: string;
  color: string;
}

const AGENT_NODES: AgentNode[] = [
  {
    id: "planner",
    name: "Planner Agent",
    role: "Query Decomposition",
    icon: Brain,
    description: "Deconstructs high-level queries into atomic investigative questions.",
    color: "from-blue-500 to-indigo-600",
  },
  {
    id: "retrieval",
    name: "Retrieval Agent",
    role: "Hybrid Search Fusion",
    icon: Search,
    description: "Executes dense vector search (Qdrant) and sparse BM25 with RRF rank fusion.",
    color: "from-indigo-500 to-purple-600",
  },
  {
    id: "evidence",
    name: "Evidence Miner",
    role: "Passage Extraction",
    icon: FileText,
    description: "Segments source documents into sliding window chunks with SHA-256 hashes.",
    color: "from-purple-500 to-pink-600",
  },
  {
    id: "critic",
    name: "Critic Agent",
    role: "NLI & Grounding",
    icon: ShieldAlert,
    description: "Performs claim-to-passage audit, contradiction detection, and gap analysis.",
    color: "from-amber-500 to-orange-600",
  },
  {
    id: "synthesis",
    name: "Synthesis Agent",
    role: "Report Compilation",
    icon: Sparkles,
    description: "Compiles verified claims into publication Markdown with traceable citations.",
    color: "from-emerald-500 to-teal-600",
  },
];

interface AgentDagViewerProps {
  currentStage: string;
  status: string;
  evidenceCount?: number;
}

export function AgentDagViewer({
  currentStage,
  status,
  evidenceCount = 0,
}: AgentDagViewerProps) {
  // Determine status of each agent node based on the pipeline stage
  const getNodeState = (index: number) => {
    if (status === "completed" || status === "ready") return "completed";
    if (status === "failed") return index === 0 ? "failed" : "idle";

    // Map stages:
    // working -> planner (0), retrieval (1), evidence (2)
    // validating -> critic (3)
    // synthesizing -> synthesis (4)
    if (currentStage === "queued") return "idle";
    if (currentStage === "working" || currentStage === "researching") {
      if (index === 0) return "completed";
      if (index === 1) return "running";
      if (index === 2) return "running";
      return "idle";
    }
    if (currentStage === "validating") {
      if (index <= 2) return "completed";
      if (index === 3) return "running";
      return "idle";
    }
    if (currentStage === "synthesizing") {
      if (index <= 3) return "completed";
      if (index === 4) return "running";
      return "idle";
    }
    return "idle";
  };

  return (
    <Card className="border-slate-800 bg-slate-900/40">
      <CardHeader className="py-4 px-6 flex flex-row items-center justify-between border-b border-slate-800/60">
        <div>
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <GitFork className="w-4 h-4 text-blue-400" />
            <span>Autonomous Multi-Agent DAG Orchestration</span>
          </CardTitle>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time execution state across LangGraph collaborative agent cycles
          </p>
        </div>
        <div className="flex items-center gap-2">
          {evidenceCount > 0 && (
            <Badge variant="cyan" className="font-mono text-xs">
              {evidenceCount} Evidence Passages
            </Badge>
          )}
          <Badge
            variant={
              status === "completed"
                ? "success"
                : status === "researching" || status === "working"
                ? "warning"
                : "secondary"
            }
          >
            Stage: {currentStage || "idle"}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
          {AGENT_NODES.map((agent, index) => {
            const state = getNodeState(index);
            const isRunning = state === "running";
            const isCompleted = state === "completed";
            const isFailed = state === "failed";
            const Icon = agent.icon;

            return (
              <div
                key={agent.id}
                className={cn(
                  "relative rounded-xl p-4 transition-all duration-300 border flex flex-col justify-between group",
                  isRunning
                    ? "border-blue-500/80 bg-blue-950/20 shadow-lg shadow-blue-500/10 ring-1 ring-blue-500/50"
                    : isCompleted
                    ? "border-emerald-500/40 bg-emerald-950/10"
                    : isFailed
                    ? "border-red-500/50 bg-red-950/10"
                    : "border-slate-800/80 bg-slate-900/40 hover:border-slate-700"
                )}
              >
                <div>
                  {/* Top Bar: Icon & Status Badge */}
                  <div className="flex items-center justify-between mb-3">
                    <div
                      className={cn(
                        "w-9 h-9 rounded-lg flex items-center justify-center transition-transform group-hover:scale-105",
                        isRunning
                          ? "bg-blue-600 text-white shadow-md shadow-blue-600/30 animate-pulse"
                          : isCompleted
                          ? "bg-emerald-600/20 text-emerald-400 border border-emerald-500/30"
                          : "bg-slate-800 text-slate-400"
                      )}
                    >
                      <Icon className="w-4 h-4" />
                    </div>

                    {isRunning && (
                      <Badge variant="warning" className="text-[10px] px-1.5 py-0">
                        <Loader2 className="w-2.5 h-2.5 animate-spin mr-1" />
                        Active
                      </Badge>
                    )}
                    {isCompleted && (
                      <Badge variant="success" className="text-[10px] px-1.5 py-0">
                        <Check className="w-2.5 h-2.5 mr-0.5" />
                        Done
                      </Badge>
                    )}
                    {!isRunning && !isCompleted && !isFailed && (
                      <span className="text-[10px] text-slate-500 font-mono">
                        Step {index + 1}
                      </span>
                    )}
                  </div>

                  {/* Title & Role */}
                  <h4 className="text-xs font-semibold text-white tracking-wide">
                    {agent.name}
                  </h4>
                  <p className="text-[11px] font-medium text-blue-400 mt-0.5">
                    {agent.role}
                  </p>
                  <p className="text-[10px] text-slate-400 mt-2 line-clamp-2 leading-relaxed">
                    {agent.description}
                  </p>
                </div>

                {/* Arrow Connector for larger screens */}
                {index < AGENT_NODES.length - 1 && (
                  <div className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-slate-900 border border-slate-700 items-center justify-center text-slate-400">
                    <ArrowRight className="w-3 h-3" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

