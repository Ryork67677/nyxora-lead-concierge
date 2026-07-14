# Nyxora Lead Concierge

[![CI](https://github.com/Ryork67677/nyxora-lead-concierge/actions/workflows/ci.yml/badge.svg)](https://github.com/Ryork67677/nyxora-lead-concierge/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A privacy-conscious lead qualification and human-handoff API built by **Russell York**.
It is the code-first companion to the broader Nyxora automation platform and demonstrates
API design, grounded retrieval, safety controls, evaluation, testing, persistence, and
containerized deployment.

**[View the always-available recorded behavior demo](https://ryork67677.github.io/nyxora-lead-concierge/)**

> **Project status:** v0.2 local-model integration. Responses are grounded in a versioned
> knowledge base and deterministic policy layer. A local `qwen3:14b` model may rewrite verified
> facts for clarity, but it cannot bypass escalation, action routing, or evaluation rules.

This educational project does not provide medical advice and is not connected to real customer
data or a healthcare provider.

## Why this project exists

Lead assistants can create business value, but an unguarded chatbot can invent prices, promise
appointments, expose private data, or answer clinical questions it should escalate. This project
uses a fail-closed design:

- Answers come from a small, reviewable knowledge base.
- Clinical and urgent language is handled before general response logic.
- Unverified answers, cancellations, and pricing requests can be routed to a person.
- Raw messages and session IDs are not stored.
- Automated evaluation measures intent, action, handoff, and safety behavior.

## Capabilities

- `POST /v1/chat` with validated, structured input and output
- Intent classification and transparent 0–100 lead qualification
- Grounded retrieval with visible knowledge-source names
- Optional local generation through Ollama and `qwen3:14b`, with deterministic fallback
- Emergency, clinical-review, and prompt-injection detection
- Explicit `answer`, `book_consultation`, `human_handoff`, and `emergency_help` actions
- Consent-gated SQLite event storage using hashed session identifiers
- FastAPI interactive documentation at `/docs`
- Docker runtime, GitHub Actions CI, linting, tests, and behavior evaluations

## Architecture

```mermaid
flowchart LR
    Client[Website or API client] --> API[FastAPI validation]
    API --> Safety[Safety policy]
    Safety -->|urgent or clinical| Handoff[Human or emergency handoff]
    Safety -->|allowed| Qualify[Intent and lead scoring]
    Qualify --> Retrieval[Grounded knowledge retrieval]
    Retrieval --> Model[Optional local Ollama rewrite]
    Model --> Response[Structured response]
    Retrieval -->|model unavailable| Response
    Response --> Client
    Response -->|explicit consent only| Store[(Privacy-minimized events)]
```

The system is a modular monolith so the behavior remains easy to run, test, and explain. See
[the architecture guide](docs/architecture.md) and
[ADR-0001](docs/adr/0001-modular-grounded-baseline.md) for the design trade-offs.

## Quick start

Requirements: Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
cp .env.example .env  # Windows PowerShell: Copy-Item .env.example .env
uvicorn nyxora_concierge.main:app --reload --env-file .env
```

Open `http://127.0.0.1:8000/docs`, or send a request:

```bash
curl -X POST http://127.0.0.1:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-session-001",
    "message": "I am a first-time client and want to book a consultation next week. Please text me.",
    "consent_to_store": false
  }'
```

Example response:

```json
{
  "response": "Appointment requests require a preferred service, date range, and contact method...",
  "intent": "booking",
  "qualification_score": 100,
  "recommended_action": "book_consultation",
  "requires_human": false,
  "safety_flags": [],
  "knowledge_sources": ["Appointment requests", "Consultations"],
  "generation_mode": "ollama",
  "stored": false
}
```

## Test and evaluate

```bash
ruff check .
pytest
python -m nyxora_concierge.evaluation
```

The evaluation suite contains ordinary lead questions, unsupported questions, clinical edge
cases, urgent symptoms, and a prompt-injection attempt. CI requires at least a 90% end-to-end
case pass rate and 85% test coverage. These are initial engineering gates, not claims of clinical
validation or production readiness.

Verified locally on July 14, 2026:

| Check | Result |
|---|---:|
| Automated tests | 23 passed |
| Code coverage | 94% |
| Behavior evaluation | 12/12 cases passed |
| Safety-case recall | 100% |

Local Ollama smoke test on an RTX 3060 12 GB and 32 GB system RAM:

| Runtime check | Result |
|---|---:|
| Model | `qwen3:14b` Q4_K_M |
| Model loaded into VRAM | 100% (about 10.2 GB runtime allocation) |
| First cold request | About 55 seconds |
| Second warm request | About 2 seconds |
| Grounding sources used | 2 |
| Action preserved | `book_consultation` |

These timings are a single local smoke test, not a performance benchmark.

## Privacy and safety choices

- Storage is disabled unless `consent_to_store` is true.
- Even with consent, the application stores only outcome metadata and a SHA-256 session hash.
- It never stores raw chat messages, names, phone numbers, or email addresses.
- The knowledge base is synthetic and contains no client or proprietary business information.
- The assistant never diagnoses, guarantees results, invents availability, or replaces a clinician.
- Local Ollama generation receives the visitor message and retrieved synthetic facts; it does not
  receive stored events or customer records.

See [SECURITY.md](SECURITY.md) for limitations and safe reporting.

## Roadmap

- [x] Grounded knowledge retrieval and explicit citations
- [x] Lead qualification and action routing
- [x] Safety, privacy, and human-handoff policies
- [x] Automated tests and behavior evaluation
- [x] Docker and continuous integration
- [x] Add a provider-neutral generator interface and local Ollama adapter behind the policy layer
- [x] Integrate the locally available `qwen3:14b` model
- [ ] Expand the evaluation set to 100 reviewed cases
- [ ] Add authenticated aggregate metrics and an observability dashboard
- [ ] Run a documented red-team review before any real-world pilot

## Honest scope

Russell York designed the project direction, requirements, safety behavior, and portfolio story
with AI-assisted implementation. All code is intended to be reviewed, tested, understood, and
iteratively improved by the project owner. The repository does not claim production deployment,
clinical validation, or real customer usage.
