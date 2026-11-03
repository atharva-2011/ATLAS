export type ResearchDepth = "fast" | "standard" | "deep";

export type ResearchStatus =
  | "queued"
  | "researching"
  | "validating"
  | "synthesizing"
  | "completed"
  | "partially_completed"
  | "failed"
  | "cancelled";

export interface ResearchJobCreate {
  title: string;
  query: string;
  depth: ResearchDepth;
  tenant_id?: string;
}

export interface ResearchJobStatus {
  research_id: string;
  job_id?: string;
  status: ResearchStatus;
  progress_percent: number;
  stage: string;
  evidence_count?: number;
  report_available?: boolean;
  error?: string | null;
  updated_at?: string;
}

export interface EvidenceLocator {
  page?: number;
  section?: string;
  line_start?: number;
  line_end?: number;
  [key: string]: unknown;
}

export interface EvidenceRecord {
  id: string;
  source_id?: string;
  task_id?: string;
  passage: string;
  claim: string;
  locator: EvidenceLocator;
  verification_status: "verified" | "contradicted" | "unverified" | "pending";
  confidence?: number | null;
  content_hash?: string | null;
}

export interface SynthesizedReport {
  report_id: string;
  research_id: string;
  version: number;
  title: string;
  summary: string;
  markdown_content: string;
  structured_json?: {
    findings?: EvidenceRecord[];
    sections?: Array<{
      title: string;
      content: string;
      citations?: string[];
    }>;
    citations?: string[];
    contradictions?: unknown[];
    gaps?: string[];
    [key: string]: unknown;
  } | null;
  status: string;
  created_at?: string;
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  content_hash: string;
  chunks_count: number;
  status: string;
  tenant_id: string;
}

export interface MicroserviceHealth {
  name: string;
  port: number;
  url: string;
  status: "healthy" | "degraded" | "offline" | "checking";
  latencyMs?: number;
  version?: string;
  lastChecked?: string;
}

export interface AgentStageNode {
  id: string;
  name: string;
  role: string;
  status: "idle" | "running" | "completed" | "failed";
  details?: string;
}

