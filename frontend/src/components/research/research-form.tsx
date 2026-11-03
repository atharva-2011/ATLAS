"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ResearchDepth, ResearchJobCreate } from "@/lib/types";
import {
  Sparkles,
  Zap,
  Target,
  Compass,
  ArrowRight,
  Lightbulb,
} from "lucide-react";

interface ResearchFormProps {
  onSubmit: (data: ResearchJobCreate) => void;
  isLoading: boolean;
  tenantId: string;
}

const SAMPLE_PROMPTS = [
  {
    title: "Solid-State Battery Energy Density & Expansion Constraints",
    query:
      "What are the gravimetric energy density limits, volumetric expansion rates during lithiation, and critical mechanical stack pressure requirements for sulfide ceramic solid-state batteries?",
    depth: "deep" as ResearchDepth,
    tag: "Materials Science",
  },
  {
    title: "Hybrid Vector + BM25 Retrieval Fusion in Agentic Systems",
    query:
      "Analyze the empirical performance gains of Reciprocal Rank Fusion (RRF) combining dense embeddings with sparse BM25 tokenizers in mitigating RAG retrieval recall dropouts.",
    depth: "standard" as ResearchDepth,
    tag: "Information Retrieval",
  },
  {
    title: "Natural Language Inference Contradiction Detection in LLMs",
    query:
      "How do cross-encoder NLI models detect factual contradictions and ungrounded hallucinations in automated multi-agent synthesis reports?",
    depth: "standard" as ResearchDepth,
    tag: "AI / ML Safety",
  },
];

export function ResearchForm({
  onSubmit,
  isLoading,
  tenantId,
}: ResearchFormProps) {
  const [title, setTitle] = useState(
    "Solid-State Battery Energy Density and Pressure Constraints"
  );
  const [query, setQuery] = useState(
    "What are the energy density limits, volumetric expansion rates, and critical pressure requirements for solid-state batteries?"
  );
  const [depth, setDepth] = useState<ResearchDepth>("deep");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    onSubmit({
      title: title.trim() || `Research on ${query.slice(0, 40)}`,
      query: query.trim(),
      depth,
      tenant_id: tenantId,
    });
  };

  const handleSelectSample = (sample: (typeof SAMPLE_PROMPTS)[0]) => {
    setTitle(sample.title);
    setQuery(sample.query);
    setDepth(sample.depth);
  };

  return (
    <Card className="border-slate-800 bg-slate-900/60 shadow-2xl">
      <CardHeader className="p-6 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-blue-400" />
              <span>Dispatch Research Mission</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Formulate a scientific or analytical inquiry. The multi-agent cluster will decompose, retrieve, audit, and synthesize a verified briefing.
            </CardDescription>
          </div>
          <Badge variant="cyan" className="font-mono text-xs">
            Multi-Agent LangGraph
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-6 pt-2">
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Mission Title */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Mission Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Solid-State Battery Energy Constraints"
              className="w-full bg-slate-950/80 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-colors"
              required
            />
          </div>

          {/* Research Objective Query */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center justify-between">
              <span>Research Objective / Detailed Query</span>
              <span className="text-[11px] text-slate-500">
                Supports complex multi-part scientific questions
              </span>
            </label>
            <textarea
              rows={3}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter comprehensive research parameters, hypotheses, or analytical requirements..."
              className="w-full bg-slate-950/80 border border-slate-800 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-colors resize-none leading-relaxed"
              required
            />
          </div>

          {/* Depth Mode Selector */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-2">
              Exploration Depth & Verification Intensity
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                {
                  id: "fast",
                  label: "Fast Synthesis",
                  desc: "Single-hop retrieval, immediate factual pass.",
                  icon: Zap,
                },
                {
                  id: "standard",
                  label: "Standard Exploration",
                  desc: "2-iteration query refinement & NLI claim audit.",
                  icon: Target,
                },
                {
                  id: "deep",
                  label: "Deep Verification",
                  desc: "Full LangGraph cycles, gap review, and contradiction check.",
                  icon: Compass,
                },
              ].map((item) => {
                const isSelected = depth === item.id;
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setDepth(item.id as ResearchDepth)}
                    className={`flex flex-col text-left p-3 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? "border-blue-500/80 bg-blue-950/30 ring-1 ring-blue-500/40"
                        : "border-slate-800/80 bg-slate-950/40 hover:border-slate-700 hover:bg-slate-900/40"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Icon
                        className={`w-4 h-4 ${
                          isSelected ? "text-blue-400" : "text-slate-400"
                        }`}
                      />
                      <span className="text-xs font-semibold text-slate-200">
                        {item.label}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-400 leading-normal">
                      {item.desc}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Sample Inquiries Quick-Select */}
          <div className="pt-2">
            <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-2">
              <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
              <span>Or click a benchmark inquiry to auto-populate:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {SAMPLE_PROMPTS.map((sample, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectSample(sample)}
                  className="inline-flex items-center gap-1.5 text-left text-xs bg-slate-900/80 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-300 transition-colors cursor-pointer"
                >
                  <span className="font-medium text-slate-200 truncate max-w-[200px]">
                    {sample.title}
                  </span>
                  <Badge variant="cyan" className="text-[9px] py-0 px-1">
                    {sample.tag}
                  </Badge>
                </button>
              ))}
            </div>
          </div>

          {/* Submit Row */}
          <div className="pt-2 flex items-center justify-between border-t border-slate-800/60">
            <span className="text-xs text-slate-400">
              Target Tenant: <strong className="text-blue-400 font-mono">{tenantId}</strong>
            </span>
            <Button
              type="submit"
              variant="glow"
              size="md"
              isLoading={isLoading}
              className="gap-2"
            >
              <span>Dispatch Research Workflow</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

