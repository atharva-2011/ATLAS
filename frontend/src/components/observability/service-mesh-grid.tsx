"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MicroserviceHealth } from "@/lib/types";
import {
  Server,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ExternalLink,
} from "lucide-react";

interface ServiceMeshGridProps {
  services: MicroserviceHealth[];
  onRefresh: () => void;
  isRefreshing: boolean;
}

export function ServiceMeshGrid({
  services,
  onRefresh,
  isRefreshing,
}: ServiceMeshGridProps) {
  return (
    <Card className="border-slate-800 bg-slate-900/60 shadow-2xl">
      <CardHeader className="p-6 pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Server className="w-4 h-4 text-blue-400" />
              <span>ATLAS Microservice Topology & Observability Mesh</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Direct telemetry from the 6 decoupled microservices operating on ports 8000–8005.
            </CardDescription>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            isLoading={isRefreshing}
            className="text-xs gap-1.5 self-start sm:self-auto"
          >
            <RefreshCw className="w-3.5 h-3.5 text-blue-400" />
            <span>Poll Mesh Health</span>
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-6 pt-2">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {services.map((svc) => {
            const isHealthy = svc.status === "healthy";
            const isDegraded = svc.status === "degraded";

            return (
              <div
                key={svc.port}
                className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 flex flex-col justify-between space-y-3 hover:border-slate-700 transition-colors"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono font-semibold text-blue-400 bg-blue-950/50 px-2 py-0.5 rounded border border-blue-500/20">
                      :{svc.port}
                    </span>

                    <Badge
                      variant={
                        isHealthy
                          ? "success"
                          : isDegraded
                          ? "warning"
                          : "destructive"
                      }
                      className="text-[10px] px-2 py-0.5 capitalize font-mono"
                    >
                      {isHealthy ? (
                        <>
                          <CheckCircle2 className="w-2.5 h-2.5 mr-1" />
                          <span>Operational</span>
                        </>
                      ) : isDegraded ? (
                        <>
                          <AlertTriangle className="w-2.5 h-2.5 mr-1" />
                          <span>Degraded</span>
                        </>
                      ) : (
                        <>
                          <XCircle className="w-2.5 h-2.5 mr-1" />
                          <span>Offline</span>
                        </>
                      )}
                    </Badge>
                  </div>

                  <h4 className="text-sm font-semibold text-white">
                    {svc.name}
                  </h4>
                  <p className="text-[11px] text-slate-400 font-mono mt-0.5 truncate">
                    http://127.0.0.1:{svc.port}/health/live
                  </p>
                </div>

                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400 font-mono">
                  <span>
                    Latency:{" "}
                    <strong
                      className={
                        (svc.latencyMs || 0) < 50
                          ? "text-emerald-400"
                          : "text-amber-400"
                      }
                    >
                      {svc.latencyMs !== undefined ? `${svc.latencyMs}ms` : "—"}
                    </strong>
                  </span>
                  <a
                    href={`http://127.0.0.1:${svc.port}/docs`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
                  >
                    <span>Swagger API</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

