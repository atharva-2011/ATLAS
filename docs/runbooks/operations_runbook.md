# ATLAS Production Operations & Runbook

This document outlines the standard operational procedures, deployment architecture, disaster recovery steps, and incident management runbooks for the ATLAS Multi-Agent Research Intelligence platform.

---

## 1. Architecture & Service Topology

ATLAS consists of six decoupled microservices and four backing datastores:

| Component | Default Port | Responsibility | Backing Store |
| :--- | :---: | :--- | :--- |
| **API Gateway** | `8000` | Ingress routing, auth, rate limiting, and request correlation | None (Stateless) |
| **Research Orchestrator** | `8001` | LangGraph workflow execution, task planning, human-in-the-loop review | PostgreSQL, Redis |
| **Ingestion Service** | `8002` | Document parsing (PDF, DOCX, TXT), chunking, content-hashing | Object Store / MinIO |
| **Retrieval Service** | `8003` | Dense vector similarity, BM25 keyword search, and Reciprocal Rank Fusion | Qdrant |
| **Agent Runtime** | `8004` | Specialized agents (Planner, Researcher, Verifier, Critic, Synthesizer) | LLM Providers |
| **Evaluation Service** | `8005` | Grounding evaluation, citation resolution audit, and quality gates | None (Stateless) |

### Datastores
- **PostgreSQL 16**: Relational repository for research runs, task checkpoints, reports, and tenant metadata.
- **Redis 7**: Distributed pub/sub and job queues for asynchronous background tasks.
- **Qdrant**: Vector database storing evidence chunk embeddings.
- **MinIO**: S3-compatible blob storage for raw documents.

---

## 2. Deployment Instructions

### Local Development / Windows PowerShell
```powershell
# 1. Environment initialization & dependency installation
.\infrastructure\scripts\setup_dev.ps1

# 2. Run all microservices locally
.\infrastructure\scripts\run_all_services.ps1

# 3. Verify health of all services
.\.venv\Scripts\python.exe infrastructure\scripts\verify_live_services.py

# 4. Graceful shutdown
.\infrastructure\scripts\stop_all_services.ps1
```

### Production Docker Compose Stack
```bash
# Copy and configure environment variables
cp .env.example .env

# Start all containers in detached mode
docker compose up -d

# Verify all services are healthy
docker compose ps
```

---

## 3. Health Checks & Probes

Every microservice implements standard Kubernetes-compliant liveness and readiness HTTP endpoints:

- **Liveness Probe**: `GET /api/v1/health/liveness`
  - Returns `200 OK` (`{"status": "alive"}`) if the process is accepting requests.
- **Readiness Probe**: `GET /api/v1/health/readiness`
  - Returns `200 OK` (`{"status": "ready", "checks": {...}}`) if dependencies (DB, Redis, Qdrant) are reachable.

---

## 4. Disaster Recovery & Backup Operations

### Creating a Snapshot Backup
To generate a timestamped, compressed, SHA-256 verified snapshot archive:
```bash
python infrastructure/scripts/backup_restore.py create --output-dir ./backups
```

### Verifying Backup Integrity
```bash
python infrastructure/scripts/backup_restore.py verify ./backups/atlas_backup_YYYYMMDD_HHMMSSZ.tar.gz
```

### Restoring from Backup
```bash
python infrastructure/scripts/backup_restore.py restore ./backups/atlas_backup_YYYYMMDD_HHMMSSZ.tar.gz --target-dir ./recovery
```

---

## 5. Metrics & Monitoring

- **Prometheus Scrape Config**: Located at [`infrastructure/monitoring/prometheus.yml`](file:///E:/ATLAS/infrastructure/monitoring/prometheus.yml).
- **Grafana Dashboard**: Import [`atlas_overview.json`](file:///E:/ATLAS/infrastructure/monitoring/grafana/dashboards/atlas_overview.json) into Grafana to monitor:
  - Throughput (QPS)
  - P95 / P99 latency percentiles
  - Active research workflows
  - Token consumption & cost rates
  - Release quality gate scores

---

## 6. Incident Response & Troubleshooting

### Scenario A: Qdrant Vector Search Unavailable / Degraded
1. Inspect Qdrant logs: `docker compose logs qdrant`
2. Test network socket connectivity: `curl -I http://localhost:6333/readyz`
3. Fallback: The `retrieval_service` degrades gracefully to sparse BM25 indexing if Qdrant is temporarily unreachable.

### Scenario B: Database Connection Exhaustion
1. Check active connections: `SELECT count(*) FROM pg_stat_activity;`
2. Adjust `DB_POOL_SIZE` and `DB_MAX_OVERFLOW` in `.env` to prevent pool saturation during peak research jobs.

### Scenario C: Model Provider Outages (OpenAI / Anthropic / Gemini)
1. The `agent_runtime` has built-in resilient fallback chains (`resilient_service_fallback_on_primary_failure`).
2. If the primary provider fails or returns a 5xx, the runtime automatically retries with the configured fallback provider and model.

