from nyxora_concierge.models import Intent, LeadContext
from nyxora_concierge.qualification import classify_intent, qualify_lead


def test_classifies_common_intents() -> None:
    assert classify_intent("Can I book an appointment?") is Intent.BOOKING
    assert classify_intent("How much does it cost?") is Intent.PRICING
    assert classify_intent("I need to reschedule") is Intent.CANCELLATION
    assert classify_intent("I need to reschedule my appointment") is Intent.CANCELLATION
    assert classify_intent("Hello there") is Intent.GENERAL


def test_scores_complete_lead_at_100() -> None:
    result = qualify_lead(
        "I want a consultation next week. Please text me; I am a first time client.",
        LeadContext(),
    )
    assert result.intent is Intent.BOOKING
    assert result.score == 100


def test_structured_context_contributes_to_score() -> None:
    result = qualify_lead(
        "Hello",
        LeadContext(
            service_interest="skin consultation",
            timeline="this month",
            contact_preference="email",
            first_visit=True,
        ),
    )
    assert result.score == 75
