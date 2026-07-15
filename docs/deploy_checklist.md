# Deploy checklist: Nyxora Lead Concierge v0.3

**Release owner:** Russell York
**Deployment shape:** One hardened container and persistent SQLite volume

## Pre-deploy

- [ ] PR reviewed and approved; CI, dependency audit, behavior evaluation, and container smoke pass
- [ ] Immutable image tag and previous rollback image recorded
- [ ] `API_KEY_HASHES` injected from a secret manager and tested without revealing the raw key
- [ ] `ALLOWED_HOSTS` contains only the deployment hostnames
- [ ] TLS reverse proxy or managed ingress configured
- [ ] SQLite volume backup completed and restoration tested
- [ ] Log destination, Prometheus scrape credentials, dashboards, and alert owner configured
- [ ] No real customer data or protected health information in the environment

## Deploy

- [ ] Start the new image as a single application process
- [ ] Confirm `/livez` and `/readyz`
- [ ] Confirm unauthenticated `/v1/chat` and `/metrics` return 401
- [ ] Run authenticated deterministic chat and safety smoke cases
- [ ] Confirm `X-Request-ID` propagation and JSON log ingestion
- [ ] Confirm HTTP, latency, response-outcome, and storage-failure metrics

## Post-deploy

- [ ] Monitor readiness, 5xx rate, p95 latency, 401 rate, and storage failures for 15 minutes
- [ ] Confirm no secrets, messages, or raw session identifiers appear in logs or metrics
- [ ] Record release evidence and close the change record

## Rollback triggers

- readiness fails twice;
- authenticated chat or safety routing fails;
- 5xx rate exceeds 2% for five minutes;
- deterministic p95 latency exceeds one second for ten minutes;
- privacy-sensitive content appears in telemetry; or
- storage failures increase after normal requests.

Follow [the operations runbook](operations_runbook.md) for rollback and restoration.
