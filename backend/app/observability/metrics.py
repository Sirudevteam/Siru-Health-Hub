# ==============================================================================
# Siru HealthHub — Prometheus Metrics Definitions
# Exports runtime metrics for Prometheus scraping: throughput, latency,
# FHIR resource counts, and auth events.
# ==============================================================================

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time

# HTTP Traffic Metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP request count",
    ["method", "endpoint", "status_code"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# FHIR Resource Inventory Metrics
FHIR_RESOURCES_COUNT = Gauge(
    "fhir_resources_count",
    "Total count of FHIR resources currently stored in PostgreSQL",
    ["resource_type"]
)

# Authentication & Security Counters
AUTH_EVENTS_TOTAL = Counter(
    "auth_events_total",
    "Security and authentication events",
    ["event_type", "result"]
)

