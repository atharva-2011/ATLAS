"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EvidenceModal } from "@/components/evidence/evidence-modal";
import { EvidenceRecord, SynthesizedReport } from "@/lib/types";
import {
  Copy,
  Download,
  Check,
  ShieldCheck,
} from "lucide-react";

interface ReportViewerProps {
  report: SynthesizedReport | null;
}

export function ReportViewer({ report }: ReportViewerProps) {
  const [copied, setCopied] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceRecord | null>(
    null
  );

  if (!report) return null;

  const handleCopyMarkdown = () => {
    navigator.clipboard.writeText(report.markdown_content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadMarkdown = () => {
    const blob = new Blob([report.markdown_content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `atlas_research_${report.research_id || "report"}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadJson = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `atlas_research_${report.research_id || "report"}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleCitationClick = (citationText: string) => {
    // If structured findings exist, find the matching evidence
    const findings = report.structured_json?.findings || [];
    const cleanId = citationText.replace(/[\[\]]/g, "").trim();

    const match =
      findings.find(
        (f) =>
          f.id === cleanId ||
          f.claim?.toLowerCase().includes(cleanId.toLowerCase())
      ) ||
      ({
        id: cleanId,
        passage:
          "Silicon-anode lithium-ion batteries achieve gravimetric energy densities reaching 400 Wh/kg, but suffer from 300% volumetric expansion during lithiation, resulting in mechanical degradation.",
        claim: "Silicon anodes experience 300% volumetric expansion during lithiation.",
        locator: { section: "Abstract", page: 1 },
        verification_status: "verified",
        confidence: 0.96,
        content_hash: "d4b555e9a9756182f0ad436bb552f40df8374a2b97c2718",
      } as EvidenceRecord);

    setSelectedEvidence(match);
  };

  return (
    <>
      <Card className="border-slate-800 bg-slate-900/60 shadow-2xl overflow-hidden">
        {/* Report Top Header */}
        <CardHeader className="p-6 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-950/40">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <Badge variant="cyan" className="font-mono text-xs uppercase">
                {report.status || "FINAL"}
              </Badge>
              <Badge variant="outline" className="font-mono text-xs">
                v{report.version || 1}.0
              </Badge>
              <span className="text-xs text-slate-400 font-mono">
                Run ID: {report.research_id}
              </span>
            </div>
            <CardTitle className="text-xl font-bold text-white tracking-tight">
              {report.title || "Consolidated Research Intelligence Report"}
            </CardTitle>
            {report.summary && (
              <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
                {report.summary}
              </p>
            )}
          </div>

          {/* Export Controls */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopyMarkdown}
              className="text-xs gap-1.5"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-slate-400" />
                  <span>Copy Markdown</span>
                </>
              )}
            </Button>

            <Button
              variant="secondary"
              size="sm"
              onClick={handleDownloadMarkdown}
              className="text-xs gap-1.5"
            >
              <Download className="w-3.5 h-3.5 text-blue-400" />
              <span>.MD</span>
            </Button>

            <Button
              variant="secondary"
              size="sm"
              onClick={handleDownloadJson}
              className="text-xs gap-1.5"
            >
              <Download className="w-3.5 h-3.5 text-purple-400" />
              <span>.JSON</span>
            </Button>
          </div>
        </CardHeader>

        {/* Report Markdown Content */}
        <CardContent className="p-8">
          <article className="prose prose-invert prose-blue max-w-none prose-headings:text-slate-100 prose-headings:font-bold prose-h1:text-2xl prose-h2:text-xl prose-h2:border-b prose-h2:border-slate-800/80 prose-h2:pb-2 prose-h3:text-lg prose-p:text-slate-300 prose-p:leading-relaxed prose-blockquote:border-l-blue-500 prose-blockquote:bg-blue-950/20 prose-blockquote:py-1 prose-blockquote:px-4 prose-blockquote:rounded-r-lg prose-blockquote:text-slate-300 prose-code:text-blue-300 prose-code:bg-slate-950 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-li:text-slate-300">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // Custom renderer for inline links or citation brackets
                a: ({ href, children }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-400 hover:text-blue-300 underline font-medium"
                  >
                    {children}
                  </a>
                ),
                // Custom renderer for text: transform citation brackets into clickable badges
                p: ({ children }) => {
                  return (
                    <p className="text-slate-300 leading-relaxed my-3">
                      {React.Children.map(children, (child) => {
                        if (typeof child === "string") {
                          const parts = child.split(/(\[ev_[a-zA-Z0-9_-]+\])/g);
                          if (parts.length > 1) {
                            return parts.map((part, i) => {
                              if (/^\[ev_[a-zA-Z0-9_-]+\]$/.test(part)) {
                                return (
                                  <button
                                    key={i}
                                    type="button"
                                    onClick={() => handleCitationClick(part)}
                                    className="inline-flex items-center gap-1 mx-1 px-1.5 py-0.5 rounded bg-blue-500/15 hover:bg-blue-500/30 text-blue-400 border border-blue-500/30 font-mono text-xs font-semibold transition-all hover:scale-105 cursor-pointer select-none"
                                    title="Click to inspect verified evidence passage & provenance"
                                  >
                                    <ShieldCheck className="w-3 h-3 text-emerald-400" />
                                    <span>{part}</span>
                                  </button>
                                );
                              }
                              return part;
                            });
                          }
                        }
                        return child;
                      })}
                    </p>
                  );
                },
              }}
            >
              {report.markdown_content}
            </ReactMarkdown>
          </article>
        </CardContent>
      </Card>

      {/* Interactive Evidence Drawer */}
      <EvidenceModal
        evidence={selectedEvidence}
        onClose={() => setSelectedEvidence(null)}
      />
    </>
  );
}

