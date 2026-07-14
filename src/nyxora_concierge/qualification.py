from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Intent, LeadContext

INTENT_TERMS: dict[Intent, tuple[str, ...]] = {
    Intent.BOOKING: ("book", "appointment", "schedule", "consultation", "availability"),
    Intent.PRICING: ("price", "pricing", "cost", "how much", "payment"),
    Intent.PREPARATION: ("prepare", "before", "pre-treatment", "pretreatment"),
    Intent.AFTERCARE: ("aftercare", "after treatment", "after my", "recovery", "side effect"),
    Intent.CANCELLATION: ("cancel", "reschedule", "move my appointment"),
    Intent.SERVICES: ("service", "treatment", "offer", "available", "option"),
}

# Specific operational intents win ties against broad words such as "appointment" or "treatment".
INTENT_PRIORITY = (
    Intent.CANCELLATION,
    Intent.AFTERCARE,
    Intent.PREPARATION,
    Intent.PRICING,
    Intent.BOOKING,
    Intent.SERVICES,
)

TIMELINE_TERMS = (
    "today",
    "tomorrow",
    "this week",
    "next week",
    "this month",
    "as soon as possible",
    "asap",
)

CONTACT_TERMS = ("call me", "text me", "email me", "phone", "sms")

SERVICE_TERMS = (
    "consultation",
    "facial",
    "injectable",
    "skin treatment",
    "laser",
    "wellness",
)


@dataclass(frozen=True, slots=True)
class QualificationResult:
    intent: Intent
    score: int


def classify_intent(message: str) -> Intent:
    text = message.casefold()
    matches = {
        intent: sum(
            bool(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text)) for term in terms
        )
        for intent, terms in INTENT_TERMS.items()
    }
    priority = {
        intent: len(INTENT_PRIORITY) - index
        for index, intent in enumerate(INTENT_PRIORITY)
    }
    intent, score = max(matches.items(), key=lambda item: (item[1], priority[item[0]]))
    return intent if score else Intent.GENERAL


def qualify_lead(message: str, context: LeadContext) -> QualificationResult:
    text = message.casefold()
    intent = classify_intent(message)
    score = 0

    if intent is not Intent.GENERAL:
        score += 25
    if context.service_interest or any(term in text for term in SERVICE_TERMS):
        score += 25
    if context.timeline or any(term in text for term in TIMELINE_TERMS):
        score += 20
    if context.contact_preference or any(term in text for term in CONTACT_TERMS):
        score += 15
    if context.first_visit is not None or "first time" in text or "new client" in text:
        score += 15

    return QualificationResult(intent=intent, score=min(score, 100))
