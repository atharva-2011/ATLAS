# ATLAS: Multi-Agent Research Intelligence System

**ATLAS** is a production-oriented, Python-based AI research intelligence platform powered by a **Microservices Architecture** and **Multi-Agent Retrieval-Augmented Generation (RAG)**.

Unlike basic search-and-summarize chatbots, ATLAS functions as a coordinated team of specialized AI agents that decompose complex research questions, execute dual-path retrieval (internal document RAG and external web research), verify every factual claim against primary source evidence, identify uncertainty and contradictions, and synthesize verified, cited research reports.

---

## Architecture Overview

ATLAS uses a **Python Monorepo** containing 6 independently deployable microservices and shared foundation packages:

```
ATLAS/
├── services/
│   ├── api_gateway/            # Port 8000: External entry point, routing, auth, rate limiting
│   ├── research_orchestrator/  # Port 8001: Workflow lifecycle, task fan-out, state machines
│   ├── ingestion_service/      # Port 8002: PDF/DOCX/TXT extraction, chunking, provenance hashing
│   ├── retrieval_service/      # Port 8003: Dense (Qdrant) + Sparse (BM25) hybrid search & reranking
│   ├── agent_runtime/          # Port 8004: LangGraph multi-agent execution (Planner, Verifier, Critic, Synthesizer)
│   └── evaluation_service/     # Port 8005: Ingestion, retrieval, citation, and groundedness benchmarking
├── shared/
│   ├── contracts/              # Versioned API schemas (HealthResponse, ReadinessResponse, ErrorResponse)
│   ├── observability/          # CorrelationIdMiddleware (X-Correlation-ID) & dual-mode structured logging
│   ├── common/                 # Core system constants and primitives
│   └── security/               # Security interfaces and token verification protocols
├── infrastructure/
│   └── scripts/                # Windows PowerShell developer automation scripts
├── tests/
│   └── integration/            # Monorepo cross-service contract & isolation tests
├── docs/                       # Architectural documentation & deployment guides
├── pyproject.toml              # Root monorepo configuration (Ruff, Pytest)
└── .env.example                # Global environment defaults template
```

---

## Service Port Map

Each microservice binds to `127.0.0.1` by default for local development isolation:

| Microservice | Default Port | Liveness Probe | Readiness Probe |
|---|---|---|---|
| **API Gateway** | `8000` | `http://127.0.0.1:8000/health/live` | `http://127.0.0.1:8000/health/ready` |
| **Research Orchestrator** | `8001` | `http://127.0.0.1:8001/health/live` | `http://127.0.0.1:8001/health/ready` |
| **Ingestion Service** | `8002` | `http://127.0.0.1:8002/health/live` | `http://127.0.0.1:8002/health/ready` |
| **Retrieval Service** | `8003` | `http://127.0.0.1:8003/health/live` | `http://127.0.0.1:8003/health/ready` |
| **Agent Runtime** | `8004` | `http://127.0.0.1:8004/health/live` | `http://127.0.0.1:8004/health/ready` |
| **Evaluation Service** | `8005` | `http://127.0.0.1:8005/health/live` | `http://127.0.0.1:8005/health/ready` |

---

## Windows PowerShell 5.1 Quickstart

### 1. Prerequisites
- **Operating System**: Windows 10/11
- **Shell**: Windows PowerShell 5.1
- **Python**: 3.12.6
- **Git**: Installed (Docker is **not** required for Phase 1)

### 2. Initial Setup
Run the automated bootstrap script to create the `.venv` virtual environment and install all packages in editable mode:

```powershell
Set-Location "E:\ATLAS"
powershell -ExecutionPolicy Bypass -File .\infrastructure\scripts\setup_dev.ps1
```

### 3. Running All Services Simultaneously
To launch all 6 services as background processes on ports 8000–8005:

```powershell
powershell -ExecutionPolicy Bypass -File .\infrastructure\scripts\run_all_services.ps1
```

To launch them with individual visible terminal windows:
```powershell
powershell -ExecutionPolicy Bypass -File .\infrastructure\scripts\run_all_services.ps1 -NewWindow
```

### 4. Stopping All Services
To cleanly terminate all running service processes and release ports 8000–8005:

```powershell
powershell -ExecutionPolicy Bypass -File .\infrastructure\scripts\stop_all_services.ps1
```

### 5. Running Quality Gates (Linting & Tests)
Run the automated test runner to execute Ruff linting, code formatting checks, and the full Pytest test suite:

```powershell
powershell -ExecutionPolicy Bypass -File .\infrastructure\scripts\test_all.ps1
```

---

## Git Branching Strategy

The repository uses a disciplined two-branch workflow:

- `main`: Production and stable release branch.
- `atharva`: Personal development branch where all active features, changes, and tests are implemented.

### Workflow:
1. All changes are made and tested on `atharva`.
2. Once verified by automated tests and quality gates, `atharva` is committed.
3. Changes from `atharva` can be merged into `main`:
   ```powershell
   git checkout main
   git merge atharva
   git checkout atharva
   ```

---

## Phase 1 Acceptance Status

- [x] Python 3.12.6 virtual environment verified on Windows.
- [x] Monorepo structure with 6 independent service packages and 4 shared packages.
- [x] Independent `pyproject.toml` and `.env.example` per service.
- [x] Pydantic Settings configuration driven by environment variables with zero hardcoding.
- [x] Structured console logging for PowerShell and machine-readable JSON logging.
- [x] `X-Correlation-ID` middleware implemented and verified across all services.
- [x] Standardized `/health/live` and `/health/ready` endpoints returning typed schemas.
- [x] Architectural isolation: Zero cross-service private imports enforced via AST integration tests.
- [x] Simultaneous live multi-process local execution verified over HTTP.
- [x] 100% test pass rate across 66 unit and integration tests.
- [x] Zero external infrastructure dependencies (No Docker, external DB, or API keys required for Phase 1).

