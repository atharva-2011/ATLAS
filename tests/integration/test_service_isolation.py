"""Integration test verifying architectural isolation: services never import from other services."""

import ast
from pathlib import Path

SERVICE_NAMES = [
    "api_gateway",
    "research_orchestrator",
    "ingestion_service",
    "retrieval_service",
    "agent_runtime",
    "evaluation_service",
]


def test_no_cross_service_imports():
    root = Path(__file__).resolve().parent.parent.parent
    services_dir = root / "services"

    for service_name in SERVICE_NAMES:
        service_path = services_dir / service_name / "src"
        other_services = [s for s in SERVICE_NAMES if s != service_name]

        for py_file in service_path.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for forbidden in other_services:
                            assert not alias.name.startswith(forbidden), (
                                f"Architectural violation: {py_file} imports forbidden service '{forbidden}'"
                            )
                elif isinstance(node, ast.ImportFrom) and node.module:
                    for forbidden in other_services:
                        assert not node.module.startswith(forbidden), (
                            f"Architectural violation: {py_file} imports from forbidden service '{forbidden}'"
                        )
