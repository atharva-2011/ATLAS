"use client";

import React, { useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { uploadDocument } from "@/lib/api";
import { DocumentUploadResponse } from "@/lib/types";
import { truncateHash } from "@/lib/utils";
import {
  UploadCloud,
  FileCheck,
  CheckCircle2,
  AlertCircle,
  Sparkles,
} from "lucide-react";

interface DocumentUploaderProps {
  tenantId: string;
  onUploadSuccess?: (doc: DocumentUploadResponse) => void;
}

export function DocumentUploader({
  tenantId,
  onUploadSuccess,
}: DocumentUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<DocumentUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setError(null);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);
    try {
      const res = await uploadDocument(file, tenantId);
      setResult(res);
      onUploadSuccess?.(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  const handleLoadSample = () => {
    const sampleContent =
      "Silicon-anode lithium-ion batteries achieve gravimetric energy densities reaching 400 Wh/kg, " +
      "but suffer from 300% volumetric expansion during lithiation, resulting in mechanical degradation. " +
      "Solid-state electrolyte interfaces using sulfide ceramic separators reduce dendrite penetration " +
      "at current densities up to 10 mA/cm2 when operated under 5 MPa stack pressure. " +
      "Commercial mass production scaling hinges on continuous mechanical pressure containment solutions.";

    const sampleFile = new File([sampleContent], "solid_state_battery_study.txt", {
      type: "text/plain",
    });
    setFile(sampleFile);
    setError(null);
  };

  return (
    <Card className="border-slate-800 bg-slate-900/60 shadow-2xl">
      <CardHeader className="p-6 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <UploadCloud className="w-4 h-4 text-blue-400" />
              <span>Knowledge Base Ingestion & Chunking Pipeline</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Upload research whitepapers, studies, and datasets (.txt, .pdf, .docx, .md). The Ingestion Service calculates cryptographic hashes, extracts passages, and indexes into Qdrant & BM25.
            </CardDescription>
          </div>
          <Badge variant="cyan" className="font-mono text-xs">
            Dual Vector + Sparse
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-6 pt-2 space-y-4">
        {/* Dropzone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleFileDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
            isDragging
              ? "border-blue-500 bg-blue-950/30 scale-[1.01]"
              : file
              ? "border-emerald-500/50 bg-emerald-950/10"
              : "border-slate-800 bg-slate-950/40 hover:border-slate-700 hover:bg-slate-900/40"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".txt,.pdf,.docx,.md"
            onChange={handleFileChange}
          />

          <div className="flex flex-col items-center justify-center space-y-2">
            <div className="w-12 h-12 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              {file ? (
                <FileCheck className="w-6 h-6 text-emerald-400" />
              ) : (
                <UploadCloud className="w-6 h-6 text-blue-400" />
              )}
            </div>

            {file ? (
              <div className="text-center">
                <p className="text-sm font-semibold text-white">{file.name}</p>
                <p className="text-xs text-slate-400 mt-0.5">
                  {(file.size / 1024).toFixed(1)} KB • Ready for extraction
                </p>
              </div>
            ) : (
              <div className="text-center">
                <p className="text-sm font-medium text-slate-200">
                  Drop files here or <span className="text-blue-400 underline">browse</span>
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Supported formats: PDF, DOCX, TXT, Markdown (Max: 50MB)
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Quick Sample File Button */}
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Need sample research data?</span>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleLoadSample}
            className="text-xs text-blue-400 hover:text-blue-300 gap-1"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Load Solid-State Battery Sample (.txt)</span>
          </Button>
        </div>

        {/* Upload Button */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
          <div className="text-xs text-slate-400">
            Active Tenant: <strong className="text-blue-400 font-mono">{tenantId}</strong>
          </div>
          <Button
            variant="glow"
            size="md"
            disabled={!file}
            isLoading={isUploading}
            onClick={handleUpload}
            className="gap-2"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Process & Index Document</span>
          </Button>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="p-3 rounded-lg bg-red-950/20 border border-red-500/40 text-xs text-red-300 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Success Card */}
        {result && (
          <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/40 text-xs space-y-2 animate-in fade-in-50 duration-200">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-emerald-300 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Document Ingestion Succeeded</span>
              </span>
              <Badge variant="success" className="font-mono text-[10px]">
                Indexed & Ready
              </Badge>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 font-mono text-[11px] pt-1">
              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800">
                <span className="text-slate-500 block">Document ID</span>
                <span className="text-slate-200 truncate block">
                  {result.document_id}
                </span>
              </div>
              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800">
                <span className="text-slate-500 block">Extracted Chunks</span>
                <span className="text-cyan-400 font-bold block">
                  {result.chunks_count || 1} passages
                </span>
              </div>
              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800">
                <span className="text-slate-500 block">Content Hash</span>
                <span className="text-blue-400 truncate block">
                  {truncateHash(result.content_hash, 16)}
                </span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

