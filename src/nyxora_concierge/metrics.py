from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest


class ServiceMetrics:
    """Application-scoped Prometheus metrics with low-cardinality labels."""

    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.http_requests = Counter(
            "nyxora_http_requests_total",
            "HTTP requests completed by method, route, and status.",
            ("method", "route", "status"),
            registry=self.registry,
        )
        self.http_duration = Histogram(
            "nyxora_http_request_duration_seconds",
            "HTTP request duration by method and route.",
            ("method", "route"),
            registry=self.registry,
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
        )
        self.concierge_responses = Counter(
            "nyxora_concierge_responses_total",
            "Concierge responses by bounded operational outcome.",
            ("intent", "action", "generation_mode", "requires_human"),
            registry=self.registry,
        )
        self.storage_failures = Counter(
            "nyxora_storage_failures_total",
            "Consent-gated persistence attempts that failed.",
            registry=self.registry,
        )

    def record_http(self, method: str, route: str, status_code: int, duration: float) -> None:
        self.http_requests.labels(method, route, str(status_code)).inc()
        self.http_duration.labels(method, route).observe(duration)

    def record_response(
        self,
        *,
        intent: str,
        action: str,
        generation_mode: str,
        requires_human: bool,
    ) -> None:
        self.concierge_responses.labels(
            intent,
            action,
            generation_mode,
            str(requires_human).lower(),
        ).inc()

    def record_storage_failure(self) -> None:
        self.storage_failures.inc()

    def render(self) -> bytes:
        return generate_latest(self.registry)
