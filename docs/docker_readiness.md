# Docker Readiness & Host Constraints

## Host Environment
- **Operating System**: Windows 10/11
- **Host Physical Memory**: 8 GB RAM
- **Docker State**: Docker Desktop is not currently installed or running on this machine.

## Phase 1 Strategy
Phase 1 intentionally avoids any dependency on Docker. All 6 microservices run natively as lightweight Python processes using Windows PowerShell 5.1 and Python 3.12.6.

Each Uvicorn service process idles at approximately 35–45 MB of RAM, allowing all 6 services to run concurrently within ~250 MB total memory footprint.

## Future Docker Containerization Roadmap (Phase 13)
When Docker is introduced in future operational phases:
1. **WSL2 Backend**: Docker Desktop should be configured with the WSL2 engine for Windows compatibility.
2. **Memory Limits**: Because the host has 8 GB RAM, container memory limits must be configured (e.g. allocating no more than 512 MB to API Gateway and lightweight services, and reserving headroom for embedding models).
3. **Multi-Stage Dockerfiles**: Dockerfiles will use multi-stage builds (`python:3.12-slim`) with non-root runtime users.
4. **Independent Images**: Each microservice will build its own container image using its specific `pyproject.toml` rather than bundling the entire monorepo into a single bloated container.
