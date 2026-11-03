"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Search,
  Sliders,
  Database,
  Binary,
  ArrowRight,
} from "lucide-react";

interface SearchMatch {
  passage: string;
  source: string;
  denseScore: number;
  sparseScore: number;
  rrfScore: number;
  locator: string;
}

const DEMO_MATCHES: SearchMatch[] = [
  {
    passage:
      "Silicon-anode lithium-ion batteries achieve gravimetric energy densities reaching 400 Wh/kg, but suffer from 300% volumetric expansion during lithiation, resulting in mechanical degradation.",
    source: "solid_state_battery_study.txt",
    denseScore: 0.94,
    sparseScore: 0.88,
    rrfScore: 0.92,
    locator: "Section 1.1 / Page 1",
  },
  {
    passage:
      "Solid-state electrolyte interfaces using sulfide ceramic separators reduce dendrite penetration at current densities up to 10 mA/cm2 when operated under 5 MPa stack pressure.",
    source: "solid_state_battery_study.txt",
    denseScore: 0.91,
    sparseScore: 0.82,
    rrfScore: 0.87,
    locator: "Section 2.4 / Page 2",
  },
  {
    passage:
      "Commercial mass production scaling hinges on continuous mechanical pressure containment solutions and automated roll-to-roll manufacturing.",
    source: "battery_manufacturing_scaling.pdf",
    denseScore: 0.79,
    sparseScore: 0.85,
    rrfScore: 0.81,
    locator: "Section 4.0 / Page 8",
  },
];

export function HybridSearchSandbox() {
  const [query, setQuery] = useState(
    "What are the pressure requirements and expansion limits of silicon anodes?"
  );
  const [vectorWeight, setVectorWeight] = useState(0.6);
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<SearchMatch[]>(DEMO_MATCHES);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSearching(true);
    setTimeout(() => {
      // Simulate real-time rank fusion calculation
      const updated = DEMO_MATCHES.map((item) => ({
        ...item,
        rrfScore: Number(
          (item.denseScore * vectorWeight + item.sparseScore * (1 - vectorWeight)).toFixed(2)
        ),
      })).sort((a, b) => b.rrfScore - a.rrfScore);

      setResults(updated);
      setIsSearching(false);
    }, 400);
  };

  return (
    <Card className="border-slate-800 bg-slate-900/60 shadow-2xl">
      <CardHeader className="p-6 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Search className="w-4 h-4 text-purple-400" />
              <span>Hybrid Search Fusion Sandbox (Dense Vector + BM25 Sparse)</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Simulate Reciprocal Rank Fusion (RRF) between Qdrant semantic embeddings and BM25 lexical token indices in real time.
            </CardDescription>
          </div>
          <Badge variant="cyan" className="font-mono text-xs">
            RRF k=60 Fusion
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-6 pt-2 space-y-5">
        {/* Search Input */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter search phrase to test hybrid fusion..."
              className="w-full bg-slate-950/80 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-colors"
            />
          </div>
          <Button type="submit" variant="glow" size="md" isLoading={isSearching}>
            <span>Simulate RRF</span>
            <ArrowRight className="w-4 h-4" />
          </Button>
        </form>

        {/* Fusion Weight Sliders */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-300 flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-blue-400" />
              <span>Fusion Bias: Dense Vector vs Sparse Lexical</span>
            </span>
            <span className="font-mono text-blue-400">
              Dense: {Math.round(vectorWeight * 100)}% | Sparse:{" "}
              {Math.round((1 - vectorWeight) * 100)}%
            </span>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-[11px] text-slate-400 font-mono flex items-center gap-1">
              <Binary className="w-3 h-3 text-purple-400" />
              <span>BM25 Sparse</span>
            </span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={vectorWeight}
              onChange={(e) => setVectorWeight(parseFloat(e.target.value))}
              className="flex-1 accent-purple-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
            />
            <span className="text-[11px] text-slate-400 font-mono flex items-center gap-1">
              <Database className="w-3 h-3 text-blue-400" />
              <span>Vector Dense</span>
            </span>
          </div>
        </div>

        {/* Results List */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Retrieved Evidence Passages (Ranked by RRF)</span>
            <span>{results.length} Candidates</span>
          </div>

          <div className="space-y-2.5">
            {results.map((match, idx) => (
              <div
                key={idx}
                className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-2 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <Badge variant="cyan" className="font-mono text-[10px]">
                      Rank #{idx + 1}
                    </Badge>
                    <span className="text-slate-300 font-medium truncate max-w-[220px]">
                      {match.source}
                    </span>
                    <span className="text-slate-500 font-mono text-[11px]">
                      {match.locator}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 font-mono text-[11px]">
                    <span className="text-blue-400">Dense: {match.denseScore}</span>
                    <span className="text-purple-400">BM25: {match.sparseScore}</span>
                    <Badge variant="success" className="font-mono text-xs">
                      RRF: {match.rrfScore}
                    </Badge>
                  </div>
                </div>

                <p className="text-xs text-slate-300 italic pl-3 border-l-2 border-purple-500/50 leading-relaxed">
                  &ldquo;{match.passage}&rdquo;
                </p>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

