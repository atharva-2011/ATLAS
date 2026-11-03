"use client";

import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { ResearchJobStatus } from "@/lib/types";
import { formatSeconds } from "@/lib/utils";
import {
  Clock,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Terminal,
  Activity,
} from "lucide-react";

interface WorkflowTimelineProps {
  jobStatus: ResearchJobStatus | null;
  onCancel?: () => void;
  isCancelling?: boolean;
}

export function WorkflowTimeline({
  jobStatus,
  onCancel,
  isCancelling = false,
}: WorkflowTimelineProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!jobStatus) {
      setElapsed(0);
      return;
    }

    const isFinished =
      jobStatus.status === "completed" ||
      jobStatus.status === "failed" ||
      jobStatus.status === "cancelled";

    if (isFinished) return;

    const interval = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [jobStatus]);

  if (!jobStatus) return null;

  const isCompleted = jobStatus.status === "completed";
  const isFailed = jobStatus.status === "failed";
  const isRunning =
    jobStatus.status === "researching" ||
    jobStatus.status === "queued" ||
    jobStatus.status === "validating" ||
    jobStatus.status === "synthesizing";

  return (
    <Card className="border-slate-800 bg-slate-900/60 shadow-xl overflow-hidden">
      <CardContent className="p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="relative">
              {isRunning && (
                <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
                  <Loader2 className="w-5 h-5 animate-spin" />
                </div>
              )}
              {isCompleted && (
                <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
              )}
              {isFailed && (
                <div className="w-9 h-9 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400">
                  <AlertCircle className="w-5 h-5" />
                </div>
              )}
            </div>

            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-white">
                  Research Mission Execution
                </span>
                <Badge
                  variant={
                    isCompleted
                      ? "success"
                      : isFailed
                      ? "destructive"
                      : "warning"
                  }
                  className="font-mono text-xs uppercase"
                >
                  {jobStatus.status}
                </Badge>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                ID: {jobStatus.research_id || jobStatus.job_id}
              </p>
            </div>
          </div>

          {/* Metrics / Timer */}
          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="flex items-center gap-1.5 text-slate-300 bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>Elapsed: {formatSeconds(elapsed)}</span>
            </div>

            <div className="flex items-center gap-1.5 text-slate-300 bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800">
              <Activity className="w-3.5 h-3.5 text-blue-400" />
              <span>{jobStatus.progress_percent}%</span>
            </div>

            {isRunning && onCancel && (
              <Button
                variant="outline"
                size="sm"
                onClick={onCancel}
                isLoading={isCancelling}
                className="text-xs text-red-400 hover:text-red-300 hover:border-red-500/50"
              >
                Cancel Run
              </Button>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-[11px] text-slate-400">
            <span className="capitalize">
              Active Stage: <strong className="text-blue-400">{jobStatus.stage || "initializing"}</strong>
            </span>
            <span>{jobStatus.progress_percent}% Complete</span>
          </div>
          <Progress value={jobStatus.progress_percent} />
        </div>

        {/* Live Event Log Stream */}
        <div className="mt-4 bg-slate-950/80 rounded-lg p-3 border border-slate-800/80 font-mono text-[11px] text-slate-300 space-y-1">
          <div className="flex items-center gap-2 text-slate-500 border-b border-slate-800/60 pb-1 mb-1">
            <Terminal className="w-3.5 h-3.5 text-slate-400" />
            <span>Agent Orchestration Telemetry Stream</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-500">[{new Date().toLocaleTimeString()}]</span>
            <span className="text-blue-400">&gt;&gt;</span>
            <span>
              {isRunning
                ? `Agent cluster collaborating on stage '${jobStatus.stage}'...`
                : isCompleted
                ? "Full research synthesis verified. Final publication report generated."
                : `Execution halted with status: ${jobStatus.status}`}
            </span>
          </div>
          {jobStatus.evidence_count !== undefined && (
            <div className="flex items-center gap-2 text-cyan-400">
              <span className="text-slate-500">[{new Date().toLocaleTimeString()}]</span>
              <span>&gt;&gt; Evidence Repository: {jobStatus.evidence_count} passages extracted & verified.</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

