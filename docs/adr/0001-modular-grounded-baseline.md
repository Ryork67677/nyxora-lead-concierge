# ADR-0001: Start with a modular grounded baseline

**Status:** Accepted  
**Date:** 2026-07-14  
**Decider:** Russell York

## Context

The portfolio needs to demonstrate API engineering, AI evaluation, safety, and deployment without
requiring paid model access or exposing real Nyxora data. It must be understandable by one early-
career developer, runnable on a laptop, and safe by default for a med-spa-shaped demonstration.

## Decision

Build a FastAPI modular monolith with deterministic policies, a versioned synthetic knowledge
base, SQLite metadata storage, and an automated behavior evaluation suite. Add any model provider
later through a narrow adapter, after the safety and evaluation boundaries exist.

## Options considered

### Option A: Modular grounded baseline

| Dimension | Assessment |
|---|---|
| Complexity | Low to medium |
| Cost | No required hosted services |
| Testability | High and deterministic |
| Portfolio value | Strong API, safety, testing, and architecture evidence |
| Natural-language flexibility | Limited until a model adapter is added |

**Pros:** Runnable offline, easy to explain, reviewable behavior, reliable CI, safer foundation.  
**Cons:** Template-like responses and simple lexical retrieval.

### Option B: Direct hosted-LLM chatbot

| Dimension | Assessment |
|---|---|
| Complexity | Low prototype complexity; higher safety complexity |
| Cost | Usage-based API expense |
| Testability | Nondeterministic without additional controls |
| Portfolio value | Demonstrates provider integration |
| Natural-language flexibility | High |

**Pros:** More conversational responses and fast initial demonstration.  
**Cons:** Provider dependence, harder evaluation, possible hallucinations, and requires secrets.

### Option C: Multi-service production architecture

| Dimension | Assessment |
|---|---|
| Complexity | High |
| Cost | Multiple deployment and data services |
| Testability | High setup burden |
| Portfolio value | Can look impressive but exceeds current needs |
| Natural-language flexibility | Depends on model layer |

**Pros:** Independent scaling and stronger production separation.  
**Cons:** Premature operational burden and harder for one developer to maintain.

## Trade-off analysis

Option A creates the strongest learning sequence: first make policy and measurement reliable,
then add model flexibility, then scale only when usage requires it. It gives up conversational
quality in v0.1 to gain explainability, repeatability, and a safer development boundary.

## Consequences

- Core behavior can be tested without network access or credentials.
- Model integration must conform to existing structured actions and safety policies.
- SQLite will need replacement if concurrent production use becomes a requirement.
- Retrieval quality must later be measured on a larger, reviewed dataset.

## Action items

1. [x] Implement the API, policies, retrieval, storage, tests, and evaluation suite.
2. [ ] Define a provider-neutral model protocol and adversarial tests.
3. [ ] Add one model adapter without allowing it to choose safety or emergency actions.
4. [ ] Review 100 evaluation cases before considering a pilot.

