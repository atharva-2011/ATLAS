"""Prometheus-compatible in-memory metrics registry for ATLAS microservices."""

import threading
from collections import defaultdict


class MetricsRegistry:
    """Thread-safe, lightweight Prometheus metrics collector without heavy external C-dependencies."""

    def __init__(self, service_name: str = "atlas") -> None:
        self.service_name = service_name
        self._lock = threading.Lock()
        self._counters: dict[str, dict[tuple, float]] = defaultdict(lambda: defaultdict(float))
        self._gauges: dict[str, dict[tuple, float]] = defaultdict(lambda: defaultdict(float))
        self._histograms: dict[str, dict[tuple, list[float]]] = defaultdict(lambda: defaultdict(list))

    def inc_counter(self, name: str, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        """Increment a counter metric."""
        lbl_tuple = tuple(sorted((labels or {}).items()))
        with self._lock:
            self._counters[name][lbl_tuple] += value

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Set a gauge metric value."""
        lbl_tuple = tuple(sorted((labels or {}).items()))
        with self._lock:
            self._gauges[name][lbl_tuple] = value

    def observe_histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Record a histogram sample (e.g. latency in seconds)."""
        lbl_tuple = tuple(sorted((labels or {}).items()))
        with self._lock:
            # Bound memory by keeping last 1000 samples per label set
            samples = self._histograms[name][lbl_tuple]
            samples.append(value)
            if len(samples) > 1000:
                del samples[0]

    def generate_prometheus_format(self) -> str:
        """Renders standard Prometheus plain-text metrics exposition format."""
        lines = []

        with self._lock:
            # Export Counters
            for name, label_dict in self._counters.items():
                metric_name = f"atlas_{name}"
                lines.append(f"# TYPE {metric_name} counter")
                for lbl_tuple, val in label_dict.items():
                    lbl_dict = dict(lbl_tuple)
                    lbl_dict.setdefault("service", self.service_name)
                    lbl_str = ",".join(f'{k}="{v}"' for k, v in sorted(lbl_dict.items()))
                    lines.append(f"{metric_name}{{{lbl_str}}} {val}")

            # Export Gauges
            for name, label_dict in self._gauges.items():
                metric_name = f"atlas_{name}"
                lines.append(f"# TYPE {metric_name} gauge")
                for lbl_tuple, val in label_dict.items():
                    lbl_dict = dict(lbl_tuple)
                    lbl_dict.setdefault("service", self.service_name)
                    lbl_str = ",".join(f'{k}="{v}"' for k, v in sorted(lbl_dict.items()))
                    lines.append(f"{metric_name}{{{lbl_str}}} {val}")

            # Export Histograms (Count and Sum)
            for name, label_dict in self._histograms.items():
                metric_name = f"atlas_{name}"
                lines.append(f"# TYPE {metric_name} histogram")
                for lbl_tuple, samples in label_dict.items():
                    lbl_dict = dict(lbl_tuple)
                    lbl_dict.setdefault("service", self.service_name)
                    lbl_str = ",".join(f'{k}="{v}"' for k, v in sorted(lbl_dict.items()))
                    count = len(samples)
                    total_sum = sum(samples)
                    lines.append(f"{metric_name}_count{{{lbl_str}}} {count}")
                    lines.append(f"{metric_name}_sum{{{lbl_str}}} {total_sum:.4f}")

        return "\n".join(lines) + "\n"


# Global singleton instance
_GLOBAL_REGISTRY: MetricsRegistry | None = None
_REGISTRY_LOCK = threading.Lock()


def get_metrics_registry(service_name: str = "atlas") -> MetricsRegistry:
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        with _REGISTRY_LOCK:
            if _GLOBAL_REGISTRY is None:
                _GLOBAL_REGISTRY = MetricsRegistry(service_name=service_name)
    return _GLOBAL_REGISTRY
