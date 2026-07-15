# ADR-0003: Harden the modular monolith for a single-instance production pilot

**Status:** Accepted

**Date:** 2026-07-15
**Decider:** Russell York

## Context

Nyxora Lead Concierge began as a local portfolio system demonstrating grounded retrieval,
deterministic safety policy, optional local-model generation, evaluation, and privacy-minimized
persistence. The next engineering goal is to demonstrate a credible path toward production software
without claiming that the system is ready for healthcare data or prematurely splitting a small
service into microservices.

The current constraints are:

- no protected health information or real customer data;
- a small HTTP surface with one business endpoint;
- optional local Ollama generation that must remain a non-critical dependency;
- SQLite persistence suitable only for one application instance; and
- a portfolio environment without an external identity provider or managed observability stack.

## Decision

Keep the modular monolith and add production controls at its real trust boundaries:

1. Require opaque bearer API keys in production. Store only configured SHA-256 digests and compare
   them in constant time. Multiple digests permit rotation. Development may run without a key.
2. Emit JSON request logs with generated or validated request IDs. Never log authorization values,
   raw messages, raw session IDs, or request bodies.
3. Expose low-cardinality Prometheus metrics for HTTP traffic, latency, concierge outcomes, and
   storage failures. Protect `/metrics` whenever authentication is configured.
4. Separate liveness (`/livez`) from dependency-aware readiness (`/readyz`). Preserve `/health` as
   a deprecated compatibility endpoint.
5. Return RFC-style problem responses for authentication, validation, storage, and unexpected
   failures. Client responses contain a request ID but not private exception details.
6. Run one non-root container with a read-only root filesystem, dropped Linux capabilities,
   bounded concurrency, a persistent data volume, and runtime-injected secrets.
7. Add dependency auditing, container smoke verification, automated dependency updates, a deploy
   checklist, and an operational rollback runbook.

## Options considered

### Authentication

| Option | Complexity | Fit now | Trade-off |
|---|---:|---:|---|
| Hashed bearer API keys | Low | High | Machine authentication and rotation, but no user roles or delegated identity |
| OAuth 2.0 / OIDC | Medium-high | Medium | Stronger identity lifecycle, but requires a trusted provider and authorization model |
| No application auth behind a proxy | Low | Low | Simple, but leaves the service unsafe when network boundaries are misconfigured |

### Service shape

| Option | Complexity | Fit now | Trade-off |
|---|---:|---:|---|
| Hardened modular monolith | Low-medium | High | One deployable unit and clear modules; vertical scaling only with SQLite |
| Microservices | High | Low | Independent scaling, but creates network, deployment, and consistency overhead without need |

### Persistence

| Option | Complexity | Fit now | Trade-off |
|---|---:|---:|---|
| SQLite with WAL, timeouts, and readiness checks | Low | High | Honest single-instance pilot boundary |
| Managed PostgreSQL | Medium | Future | Better concurrency and operations, but requires a real deployment and migration plan |

## Consequences

- Production startup fails closed when no API key digest is configured.
- The service becomes observable without collecting message content or personal identifiers.
- Operators can distinguish a live process from a process that cannot reach required storage.
- API keys remain a transitional machine-authentication mechanism, not full authorization.
- In-process metrics and SQLite constrain the deployment to one application process.
- TLS termination, rate limiting, managed secrets, backups, alert routing, and an external identity
  provider remain deployment responsibilities and are documented as production gaps.

## Action items

- [x] Add bearer authentication, JSON logs, request IDs, metrics, and problem responses.
- [x] Add liveness, readiness, hardened Compose, CI security checks, and failure-path tests.
- [x] Document deployment, rollback triggers, and remaining limitations.
- [ ] Replace API keys with OIDC before supporting multiple human operator roles.
- [ ] Migrate to managed encrypted storage before horizontal scaling or real customer data.
- [ ] Complete external security, privacy, clinical, and legal reviews before any real-world pilot.
