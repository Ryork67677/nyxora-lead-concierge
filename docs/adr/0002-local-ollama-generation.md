# ADR-0002: Use local Ollama for grounded response generation

**Status:** Accepted  
**Date:** 2026-07-14  
**Decider:** Russell York

## Context

The project needs real model integration without recurring API charges or sending demonstration
conversations to a hosted provider. The development PC already has Ollama, `qwen3:14b`, an RTX
3060 with 12 GB VRAM, and 32 GB system memory. The deterministic v0.1 safety baseline must remain
authoritative.

## Decision

Use Ollama's local `/api/chat` endpoint with `qwen3:14b` as an optional grounded response writer.
The model receives only the visitor message and retrieved synthetic facts. Deterministic code
continues to decide safety, intent, qualification score, handoff, and recommended action. A model
error triggers a verified deterministic response.

## Options considered

### Option A: Local Ollama with `qwen3:14b`

| Dimension | Assessment |
|---|---|
| Complexity | Medium |
| Cost | No per-message charge; local electricity and storage |
| Privacy | Requests stay on the development PC |
| Reliability | Depends on the local Ollama process and hardware |
| Portfolio value | Demonstrates local inference and resilient integration |

**Pros:** Existing model, no API key, local data path, deterministic fallback.  
**Cons:** Slower cold start, hardware dependency, not directly scalable across servers.

### Option B: Hosted commercial model API

| Dimension | Assessment |
|---|---|
| Complexity | Low to medium |
| Cost | Usage-based |
| Privacy | Prompts leave the local system |
| Reliability | Provider-managed infrastructure |
| Portfolio value | Demonstrates production API integration |

**Pros:** Easier scaling, strong model quality, minimal local compute.  
**Cons:** Credentials, recurring cost, provider dependency, additional data review.

### Option C: Keep deterministic responses only

| Dimension | Assessment |
|---|---|
| Complexity | Low |
| Cost | None |
| Privacy | Fully local |
| Reliability | Highly deterministic |
| Portfolio value | Strong safety baseline but limited AI evidence |

**Pros:** Fast, repeatable, simple to evaluate.  
**Cons:** Less natural responses and no inference integration evidence.

## Trade-off analysis

Option A uses hardware and models already available while preserving v0.1's testability. The model
is deliberately denied decision authority: conversational quality may improve, but all business
and safety behavior remains deterministic and auditable.

## Consequences

- The API can report `ollama`, `deterministic`, or `fallback` generation mode.
- Local development requires Ollama to be running for model-written responses.
- Docker connects to the host model service through `host.docker.internal`.
- Model quality must be evaluated separately from deterministic action-routing quality.
- A hosted adapter can be added later without changing the core service policy.

## Action items

1. [x] Implement and unit-test the Ollama adapter.
2. [x] Preserve deterministic fallback and action authority.
3. [ ] Expand response-quality and hallucination evaluations to 100 cases.
4. [x] Record initial cold/warm smoke-test latency and GPU residency.
