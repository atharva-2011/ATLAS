# ATLAS Architectural Specification

## Microservices Monorepo Design

ATLAS enforces strict microservice boundaries within a Python monorepo. This balances atomic versioning and coordinated cross-service testing with runtime independence.

### 1. Service Isolation
- Each service in `services/` is packaged as an independent Python distribution (`atlas-api-gateway`, `atlas-research-orchestrator`, etc.).
- Services **never** import private application code or internal domain models from other services.
- Inter-service communication occurs strictly via explicit, versioned HTTP APIs.
- Architectural boundary compliance is continuously enforced by automated AST tests in `tests/integration/test_service_isolation.py`.

### 2. Shared Foundation Packages
Shared libraries live in `shared/` and are strictly restricted to generic cross-cutting concerns:
- `atlas_contracts`: Versioned DTOs (`HealthResponse`, `ReadinessResponse`, `ErrorResponse`). Domain entities (e.g. `ResearchRun`, `EvidenceRecord`) are owned by specific services, preventing a "distributed monolith".
- `atlas_observability`: Context-managed request correlation (`X-Correlation-ID`) and dual-mode structured logging (human-readable console formatter for Windows PowerShell + machine-readable JSON formatter for log aggregation).
- `atlas_common`: Shared system constants and environment identifiers.
- `atlas_security`: Security context interfaces and protocol definitions.

### 3. Service Lifecycle & Health
Every service implements the standard dual-probe pattern:
- `/health/live`: Fast probe verifying that the Python process and asyncio event loop are responsive. It never checks external infrastructure (databases, caches, or vector indexes) to prevent cascade failures.
- `/health/ready`: Probe indicating whether the service has completed initialization and can accept incoming traffic.
