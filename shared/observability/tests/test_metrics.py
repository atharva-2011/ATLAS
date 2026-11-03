"""Unit tests for the MetricsRegistry and Prometheus formatter."""

from atlas_observability.metrics import MetricsRegistry, get_metrics_registry


def test_metrics_registry_singleton() -> None:
    reg1 = get_metrics_registry("test-svc")
    reg2 = get_metrics_registry("test-svc")
    assert reg1 is reg2


def test_metrics_counter_and_prometheus_format() -> None:
    reg = MetricsRegistry(service_name="api-gateway")
    reg.inc_counter("http_requests_total", 1.0, {"endpoint": "/api/v1/research", "status": "200"})
    reg.inc_counter("http_requests_total", 2.0, {"endpoint": "/api/v1/research", "status": "200"})
    reg.inc_counter("http_requests_total", 1.0, {"endpoint": "/api/v1/health", "status": "200"})

    prom = reg.generate_prometheus_format()
    assert "# TYPE atlas_http_requests_total counter" in prom
    assert 'atlas_http_requests_total{endpoint="/api/v1/research",service="api-gateway",status="200"} 3.0' in prom
    assert 'atlas_http_requests_total{endpoint="/api/v1/health",service="api-gateway",status="200"} 1.0' in prom


def test_metrics_gauge_and_histogram() -> None:
    reg = MetricsRegistry(service_name="research-orchestrator")
    reg.set_gauge("active_jobs", 5.0, {"tenant": "tenant_1"})
    reg.observe_histogram("task_duration_seconds", 1.5, {"task_type": "deep_search"})
    reg.observe_histogram("task_duration_seconds", 2.5, {"task_type": "deep_search"})

    prom = reg.generate_prometheus_format()
    assert "# TYPE atlas_active_jobs gauge" in prom
    assert 'atlas_active_jobs{service="research-orchestrator",tenant="tenant_1"} 5.0' in prom

    assert "# TYPE atlas_task_duration_seconds histogram" in prom
    assert 'atlas_task_duration_seconds_count{service="research-orchestrator",task_type="deep_search"} 2' in prom
    assert 'atlas_task_duration_seconds_sum{service="research-orchestrator",task_type="deep_search"} 4.0000' in prom

