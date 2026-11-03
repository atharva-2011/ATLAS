import {
  DocumentUploadResponse,
  MicroserviceHealth,
  ResearchJobCreate,
  ResearchJobStatus,
  SynthesizedReport,
} from "./types";

const GATEWAY_BASE_URL =
  process.env.NEXT_PUBLIC_API_GATEWAY_URL || "http://127.0.0.1:8000";

const SERVICES_REGISTRY = [
  { name: "API Gateway", port: 8000, package: "api_gateway" },
  { name: "Research Orchestrator", port: 8001, package: "research_orchestrator" },
  { name: "Ingestion Service", port: 8002, package: "ingestion_service" },
  { name: "Retrieval Service", port: 8003, package: "retrieval_service" },
  { name: "Agent Runtime", port: 8004, package: "agent_runtime" },
  { name: "Evaluation Service", port: 8005, package: "evaluation_service" },
];

export async function uploadDocument(
  file: File,
  tenantId: string = "default",
  userId: string = "analyst_web"
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("tenant_id", tenantId);

  const response = await fetch(`${GATEWAY_BASE_URL}/api/v1/documents/upload`, {
    method: "POST",
    headers: {
      "X-Tenant-ID": tenantId,
      "X-User-ID": userId,
    },
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Upload failed (${response.status}): ${errorText}`);
  }

  return response.json();
}

export async function submitResearchJob(
  payload: ResearchJobCreate,
  tenantId: string = "default",
  userId: string = "analyst_web"
): Promise<ResearchJobStatus> {
  const response = await fetch(`${GATEWAY_BASE_URL}/api/v1/research/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Tenant-ID": tenantId,
      "X-User-ID": userId,
    },
    body: JSON.stringify({
      title: payload.title,
      query: payload.query,
      depth: payload.depth,
      tenant_id: tenantId,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to submit job (${response.status}): ${errorText}`);
  }

  return response.json();
}

export async function getResearchJobStatus(
  jobId: string,
  tenantId: string = "default",
  userId: string = "analyst_web"
): Promise<ResearchJobStatus> {
  const response = await fetch(`${GATEWAY_BASE_URL}/api/v1/research/jobs/${jobId}`, {
    method: "GET",
    headers: {
      "X-Tenant-ID": tenantId,
      "X-User-ID": userId,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch job status (${response.status}): ${errorText}`);
  }

  return response.json();
}

export async function getResearchReport(
  jobId: string,
  tenantId: string = "default",
  userId: string = "analyst_web"
): Promise<SynthesizedReport> {
  const response = await fetch(
    `${GATEWAY_BASE_URL}/api/v1/research/jobs/${jobId}/report`,
    {
      method: "GET",
      headers: {
        "X-Tenant-ID": tenantId,
        "X-User-ID": userId,
      },
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to retrieve report (${response.status}): ${errorText}`);
  }

  return response.json();
}

export async function checkMicroserviceHealth(
  service: (typeof SERVICES_REGISTRY)[0]
): Promise<MicroserviceHealth> {
  const targetUrl = `http://127.0.0.1:${service.port}/health/live`;
  const start = performance.now();
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const res = await fetch(targetUrl, {
      signal: controller.signal,
      cache: "no-store",
    });
    clearTimeout(timeoutId);

    const latency = Math.round(performance.now() - start);
    if (res.ok) {
      const data = await res.json().catch(() => ({}));
      return {
        name: service.name,
        port: service.port,
        url: targetUrl,
        status: "healthy",
        latencyMs: latency,
        version: data?.version || "1.0.0",
        lastChecked: new Date().toLocaleTimeString(),
      };
    }
    return {
      name: service.name,
      port: service.port,
      url: targetUrl,
      status: "degraded",
      latencyMs: latency,
      lastChecked: new Date().toLocaleTimeString(),
    };
  } catch {
    return {
      name: service.name,
      port: service.port,
      url: targetUrl,
      status: "offline",
      lastChecked: new Date().toLocaleTimeString(),
    };
  }
}

export async function checkAllMicroservices(): Promise<MicroserviceHealth[]> {
  return Promise.all(SERVICES_REGISTRY.map(checkMicroserviceHealth));
}

