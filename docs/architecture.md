# Architecture guide

## System goal

Convert a short website conversation into a useful, reviewable next action without providing
medical advice, inventing business facts, or collecting unnecessary personal data.

## Request flow

1. **FastAPI validates input.** Session identifiers have a restricted format, messages are
   normalized, and payload sizes are bounded.
2. **Safety policy runs first.** Urgent symptoms, clinical questions, and prompt-injection phrases
   are detected before retrieval or lead qualification can generate an ordinary reply.
3. **Qualification classifies the request.** The system identifies a business intent and computes
   a transparent lead score from service interest, timeline, contact preference, and visit status.
4. **Retrieval grounds the answer.** Token overlap ranks entries from a synthetic, versioned JSON
   knowledge base. No match means no invented answer.
5. **The local model has a narrow role.** When enabled, Ollama rewrites only retrieved facts into a
   concise response. It cannot set intent, score, safety flags, handoff, or recommended action.
6. **Action routing is explicit.** Responses return a machine-readable action and handoff flag for
   future n8n or website integration.
7. **Persistence is opt-in and minimized.** With consent, only outcome metadata and a hashed
   session identifier are stored in SQLite. Raw messages are not retained.
8. **Production requests are authenticated.** Production startup requires one or more SHA-256
   bearer-key digests. The application compares supplied keys in constant time and never logs them.
9. **Operations are observable.** Request middleware adds correlation IDs, privacy-safe JSON logs,
   low-cardinality Prometheus metrics, and separate liveness and readiness signals.

## Components

| Component | Responsibility | Key failure behavior |
|---|---|---|
| `main.py` | HTTP lifecycle and endpoints | Validates and returns safe server errors |
| `auth.py` | Hashed bearer-key verification | Rejects missing or invalid credentials |
| `observability.py` | JSON logs and request context | Excludes request content and credentials |
| `metrics.py` | HTTP and business outcome metrics | Uses bounded labels to avoid cardinality growth |
| `safety.py` | Urgent, clinical, and injection policy | Routes to human or emergency help |
| `qualification.py` | Intent and lead score | Defaults to general/low confidence |
| `knowledge.py` | Reviewable retrieval | Returns no answer when ungrounded |
| `generation.py` | Local grounded rewriting | Falls back to verified deterministic text |
| `service.py` | Orchestration and action policy | Fails closed to human handoff |
| `repository.py` | Consent-gated event storage | Stores no transcript or raw session ID |
| `evaluation.py` | Repeatable behavior measurement | Fails CI below the quality gate |

## Trust boundaries

- Website input is untrusted and validated at the API boundary.
- Knowledge-base content is trusted only after repository review.
- Ollama is treated as untrusted output and is placed after safety checks and retrieval.
- SQLite is local application state and must not be publicly exposed.
- Human operators remain responsible for appointment confirmation and clinical communication.
- API-key hashes are trusted configuration; raw keys belong only in a secret manager and clients.
- Metrics and logs cross an operational trust boundary and deliberately exclude visitor content.

## Remaining production gaps

Version 0.3 is production-shaped portfolio software, not a production healthcare system. It adds
authentication, structured logging, metrics, health probes, hardened deployment, failure handling,
and release checks. A real pilot still needs TLS ingress, rate limiting, managed secrets, encrypted
managed storage, backup and retention enforcement, alert routing, OAuth/OIDC and role authorization,
penetration testing, legal/privacy review, model-provider review, and broader safety evaluation with
domain experts.
