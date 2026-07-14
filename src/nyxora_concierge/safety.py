from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SafetyResult:
    flags: tuple[str, ...] = ()
    urgent: bool = False
    requires_human: bool = False


URGENT_PHRASES = {
    "difficulty breathing",
    "can't breathe",
    "cannot breathe",
    "chest pain",
    "vision loss",
    "severe swelling",
    "unconscious",
}

CLINICAL_REVIEW_PHRASES = {
    "pregnant",
    "pregnancy",
    "breastfeeding",
    "allergic reaction",
    "infection",
    "prescription",
    "blood thinner",
    "diagnose",
}

PROMPT_ATTACK_PHRASES = {
    "ignore previous instructions",
    "ignore all instructions",
    "system prompt",
    "developer message",
    "jailbreak",
}


def evaluate_safety(message: str) -> SafetyResult:
    text = message.casefold()
    flags: list[str] = []

    if any(phrase in text for phrase in PROMPT_ATTACK_PHRASES):
        flags.append("prompt_injection")

    if any(phrase in text for phrase in URGENT_PHRASES):
        flags.append("urgent_symptoms")
        return SafetyResult(tuple(flags), urgent=True, requires_human=True)

    if any(phrase in text for phrase in CLINICAL_REVIEW_PHRASES):
        flags.append("clinical_review")

    return SafetyResult(
        tuple(flags),
        urgent=False,
        requires_human="clinical_review" in flags,
    )

