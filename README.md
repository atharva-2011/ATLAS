# ATLAS: Multi-Agent Research Intelligence System

**ATLAS** is a production-oriented, Python-first AI research intelligence platform powered by a **Microservices Architecture** and **Multi-Agent Retrieval-Augmented Generation (RAG)**.

Unlike basic search-and-summarize chatbots, ATLAS functions as an autonomous, coordinated team of specialized AI agents that decompose complex research questions, execute dual-path retrieval (internal document RAG and external web research), verify every factual claim against primary source evidence, identify uncertainty and contradictions, and synthesize verified, cited research reports.

---

## Architecture Overview

ATLAS uses a **Python Monorepo** containing 6 independently deployable microservices and 4 shared foundation packages:

```
ATLAS/
├── services/
│   ├── api_gateway/            # Port 8000: External entry point, routing, auth, rate limiting
│   ├── research_orchestrator/  # Port 8001: LangGraph state machines, async jobs, Postgres storage
│   ├── ingestion_service/      # Port 8002: PDF/DOCX/TXT extraction, chunking, provenance hashing
│   ├── retrieval_service/      # Port 8003: Dense (Qdrant) + Sparse (BM25) hybrid search (RRF)
│   ├── agent_runtime/          # Port 8004: Specialized agents (Planner, Researcher, Verifier, Critic, Synthesizer)
│   └── evaluation_service/     # Port 8005: NLI claim verification, citation auditor, ranking metrics
├── shared/
│   ├── contracts/              # Versioned API schemas, DTOs, and domain contracts
│   ├── observability/          # X-Correlation-ID middleware, structured logging, Prometheus metrics
│   ├── common/                 # Core system constants and environment configuration validator
│   └── security/               # Security interfaces, context propagation, and auth protocols
├── infrastructure/
│   ├── docker/                 # Production multi-stage Dockerfiles and .dockerignore
│   ├── monitoring/             # Prometheus scrape configs & Grafana overview dashboards
│   └── scripts/                # Automation scripts (setup, test, benchmark, backup/restore)
├── tests/
│   ├── fixtures/gold_sets/     # Curated gold standard retrieval & claim verification benchmarks
│   └── integration/            # Cross-service contracts, correlation propagation, and quality gates
├── docs/runbooks/              # Production operations, scaling, and disaster recovery runbooks
├── docker-compose.yml          # Production multi-container orchestration stack
├── pyproject.toml              # Monorepo build and test configuration (Ruff, Pytest)
└── .env.example                # Global configuration environment template
```

---

## Service Port Map

| Microservice | Port | Liveness Probe | Readiness Probe |
|---|:---:|---|---|
| **API Gateway** | `8000` | `http://127.0.0.1:8000/api/v1/health/liveness` | `http://127.0.0.1:8000/api/v1/health/readiness` |
| **Research Orchestrator** | `8001` | `http://127.0.0.1:8001/api/v1/health/liveness` | `http://127.0.0.1:8001/api/v1/health/readiness` |
| **Ingestion Service** | `8002` | `http://127.0.0.1:8002/api/v1/health/liveness` | `http://127.0.0.1:8002/api/v1/health/readiness` |
| **Retrieval Service** | `8003` | `http://127.0.0.1:8003/api/v1/health/liveness` | `http://127.0.0.1:8003/api/v1/health/readiness` |
| **Agent Runtime** | `8004` | `http://127.0.0.1:8004/api/v1/health/liveness` | `http://127.0.0.1:8004/api/v1/health/readiness` |
| **Evaluation Service** | `8005` | `http://127.0.0.1:8005/api/v1/health/liveness` | `http://127.0.0.1:8005/api/v1/health/readiness` |

---

## Implementation Roadmap Status (13 / 13 Phases Complete)

- [x] **Phase 1: Architecture & Foundation** — Microservices skeleton, Pydantic settings, correlation tracing, and isolation contracts.
- [x] **Phase 2: Data Modeling & Storage** — PostgreSQL relational schemas, SQLAlchemy models, Alembic migrations, and repositories.
- [x] **Phase 3: Document Ingestion** — PDF, DOCX, TXT structure-aware extractors, chunkers, and content-hashing.
- [x] **Phase 4: Embeddings & Vector Storage** — Embedding provider abstraction (Sentence Transformers, deterministic) & Qdrant adapter.
- [x] **Phase 5: Hybrid Retrieval & Reranking** — Dense vector search, sparse BM25 indexing, and Reciprocal Rank Fusion (RRF).
- [x] **Phase 6: LLM Provider Abstraction** — Provider adapters (OpenAI, Anthropic, Gemini, Mock), resilient retries, and fallback service.
- [x] **Phase 7: Specialized Research Agents** — Planner, Document Researcher, Web Researcher, Verifier, Critic, and Synthesizer agents.
- [x] **Phase 8: Research Orchestration** — LangGraph state machines, supervisor routers, and checkpointing.
- [x] **Phase 9: Evaluation Service** — Atomic claim extraction, directional contradiction detection, and NLI verification engine.
- [x] **Phase 10: Synthesis & Citation Reporting** — Inline citation resolvers, reference tables, and publication Markdown renderer.
- [x] **Phase 11: Async Jobs & API Gateway** — Durable background job queue, tenant security context, and proxy forwarding.
- [x] **Phase 12: Benchmarks & Quality Gates** — Curated gold sets, ranking evaluators (Recall@k, MRR, nDCG), and release scorecard CLI.
- [x] **Phase 13: Deployment, Monitoring & Operations** — Multi-stage Dockerfiles, Docker Compose, Prometheus metrics, Grafana dashboards, and disaster recovery automation.

---

## Quickstart Guide

### 1. Local Development Setup (Windows PowerShell)
```powershell
# 1. Initialize virtual environment and install all packages in editable mode
.\infrastructure\scripts\setup_dev.ps1

# 2. Launch all 6 microservices locally
.\infrastructure\scripts\run_all_services.ps1

# 3. Verify health of running services
.\.venv\Scripts\python.exe infrastructure\scripts\verify_live_services.py

# 4. Stop all running services
.\infrastructure\scripts\stop_all_services.ps1
```

### 2. Running Quality Gate Benchmarks
Run the standardized evaluation benchmark against gold datasets to verify ranking and claim verification metrics:
```powershell
.\.venv\Scripts\python.exe infrastructure\scripts\run_quality_benchmarks.py
```

### 3. Running Test Suites
Run the entire test suite across all services and integration modules:
```powershell
.\.venv\Scripts\python.exe -m pytest -v
# Or run step-by-step per service:
.\.venv\Scripts\python.exe -m pytest services\evaluation_service\tests -v
```

### 4. Running Code Hygiene & Linting
```powershell
.\.venv\Scripts\ruff.exe check .
```

### 5. Disaster Recovery & Snapshot Backups
```powershell
# Create snapshot backup
.\.venv\Scripts\python.exe infrastructure\scripts\backup_restore.py create --output-dir ./backups

# Verify snapshot integrity
.\.venv\Scripts\python.exe infrastructure\scripts\backup_restore.py verify .\backups\<archive_name>.tar.gz
```

### 6. Production Container Deployment (Docker Compose)
```bash
# Start all microservices, databases, caches, and vector stores
docker compose up -d

# Check service health status
docker compose ps
```

---

## Test Verification Summary

- **Total Monorepo Tests**: **166 / 166 Passed (100% Pass Rate)**
- **Shared Observability & Metrics**: 9 / 9 passed
- **Shared Contracts & Domain**: 7 / 7 passed
- **Shared Common & Security**: 8 / 8 passed
- **Ingestion Service**: 13 / 13 passed
- **Retrieval Service**: 18 / 18 passed
- **Agent Runtime**: 26 / 26 passed
- **Research Orchestrator**: 22 / 22 passed
- **Evaluation Service**: 25 / 25 passed
- **API Gateway**: 8 / 8 passed
- **Integration Tests**: 30 / 30 passed
- **Code Linting (`ruff`)**: Clean (0 errors)
