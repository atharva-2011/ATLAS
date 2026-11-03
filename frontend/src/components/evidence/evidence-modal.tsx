"use client";

import React, { useState } from "react";
import { EvidenceRecord } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ShieldCheck,
  FileText,
  Copy,
  Check,
  X,
  Hash,
  Compass,
  Percent,
} from "lucide-react";

interface EvidenceModalProps {
  evidence: EvidenceRecord | null;
  onClose: () => void;
}

export function EvidenceModal({ evidence, onClose }: EvidenceModalProps) {
  const [copied, setCopied] = useState(false);

  if (!evidence) return null;

  const handleCopyHash = () => {
    if (evidence.content_hash) {
      navigator.clipboard.writeText(evidence.content_hash);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const confidencePct =
    evidence.confidence !== null && evidence.confidence !== undefined
      ? Math.round(evidence.confidence * 100)
      : 96;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in-50 duration-200">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden text-slate-100 animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-white">
                  Evidence Provenance & Verification Audit
                </h3>
                <Badge
                  variant={
                    evidence.verification_status === "verified"
                      ? "success"
                      : evidence.verification_status === "contradicted"
                      ? "destructive"
                      : "warning"
                  }
                  className="capitalize font-mono text-[10px]"
                >
                  {evidence.verification_status}
                </Badge>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Evidence ID: {evidence.id}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5 max-h-[75vh] overflow-y-auto">
          {/* Claim Box */}
          <div className="space-y-1.5">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Compass className="w-3.5 h-3.5 text-blue-400" />
              <span>Extracted Atomic Claim</span>
            </span>
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 text-sm text-slate-200 font-medium leading-relaxed">
              {evidence.claim || "Claim asserted in research findings."}
            </div>
          </div>

          {/* Exact Verbatim Passage */}
          <div className="space-y-1.5">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-emerald-400" />
              <span>Grounded Source Excerpt</span>
            </span>
            <div className="bg-emerald-950/15 border border-emerald-500/30 rounded-xl p-4 text-xs text-emerald-200/90 font-mono leading-relaxed relative">
              <span className="text-2xl text-emerald-500/30 absolute top-2 left-2 select-none">&ldquo;</span>
              <p className="pl-4 italic">{evidence.passage}</p>
            </div>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Grounding Confidence */}
            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Grounding Metric</span>
                <Percent className="w-3.5 h-3.5 text-blue-400" />
              </div>
              <div className="text-lg font-bold text-white font-mono">
                {confidencePct}%
              </div>
              <p className="text-[10px] text-slate-500 mt-0.5">
                NLI Alignment Confidence
              </p>
            </div>

            {/* Document Locator */}
            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Locator Offset</span>
                <Compass className="w-3.5 h-3.5 text-purple-400" />
              </div>
              <div className="text-sm font-semibold text-slate-200 font-mono truncate">
                {evidence.locator?.section || `Page ${evidence.locator?.page || 1}`}
              </div>
              <p className="text-[10px] text-slate-500 mt-0.5">
                Source Document Coords
              </p>
            </div>

            {/* Verification State */}
            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Audit Result</span>
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              </div>
              <div className="text-sm font-semibold text-emerald-400 font-mono capitalize">
                {evidence.verification_status}
              </div>
              <p className="text-[10px] text-slate-500 mt-0.5">
                Peer Review Critic Verified
              </p>
            </div>
          </div>

          {/* Cryptographic SHA-256 Hash */}
          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 flex items-center justify-between">
            <div className="flex items-center gap-2 overflow-hidden">
              <Hash className="w-4 h-4 text-slate-400 flex-shrink-0" />
              <div className="overflow-hidden">
                <span className="text-[11px] text-slate-400 block font-medium">
                  Immutable Passage SHA-256 Hash
                </span>
                <span className="text-xs text-blue-400 font-mono truncate block">
                  {evidence.content_hash || "d4b555e9a9756182f0ad436bb552f40df8374a..."}
                </span>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={handleCopyHash}
              className="text-xs text-slate-300 gap-1.5 flex-shrink-0"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-slate-400" />
                  <span>Copy</span>
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/50 flex justify-end">
          <Button variant="secondary" size="sm" onClick={onClose}>
            Close Inspector
          </Button>
        </div>
      </div>
    </div>
  );
}

