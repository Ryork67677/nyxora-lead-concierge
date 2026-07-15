from __future__ import annotations

import logging

from .generation import GenerationError, GroundedGenerator
from .knowledge import KnowledgeBase
from .metrics import ServiceMetrics
from .models import ChatRequest, ChatResponse, GenerationMode, Intent, RecommendedAction
from .qualification import qualify_lead
from .repository import EventRepository, RepositoryError
from .safety import evaluate_safety

logger = logging.getLogger(__name__)

URGENT_RESPONSE = (
    "Your message may describe an urgent medical issue. This assistant cannot assess emergencies. "
    "Call emergency services now, or seek immediate medical care. Do not wait for a reply here."
)

CLINICAL_RESPONSE = (
    "That question needs review by a qualified clinician who can consider your medical history. "
    "I can help arrange a consultation, but I cannot diagnose conditions or provide medical advice."
)

INJECTION_RESPONSE = (
    "I can only help with Nyxora-related service and booking questions. I cannot reveal or change "
    "private system instructions. What would you like to know about consultations or scheduling?"
)

FALLBACK_RESPONSE = (
    "I do not have enough verified information to answer that confidently. I can connect you with "
    "a team member or help you request a consultation."
)


class ConciergeService:
    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        repository: EventRepository | None = None,
        generator: GroundedGenerator | None = None,
        metrics: ServiceMetrics | None = None,
    ):
        self.knowledge_base = knowledge_base
        self.repository = repository
        self.generator = generator
        self.metrics = metrics

    def respond(self, request: ChatRequest) -> ChatResponse:
        safety = evaluate_safety(request.message)
        qualification = qualify_lead(request.message, request.context)

        if safety.urgent:
            result = ChatResponse(
                response=URGENT_RESPONSE,
                intent=Intent.SAFETY,
                qualification_score=qualification.score,
                recommended_action=RecommendedAction.EMERGENCY_HELP,
                requires_human=True,
                safety_flags=list(safety.flags),
            )
        elif "prompt_injection" in safety.flags:
            result = ChatResponse(
                response=INJECTION_RESPONSE,
                intent=qualification.intent,
                qualification_score=qualification.score,
                recommended_action=RecommendedAction.ANSWER,
                requires_human=False,
                safety_flags=list(safety.flags),
            )
        elif safety.requires_human:
            result = ChatResponse(
                response=CLINICAL_RESPONSE,
                intent=Intent.SAFETY,
                qualification_score=qualification.score,
                recommended_action=RecommendedAction.HUMAN_HANDOFF,
                requires_human=True,
                safety_flags=list(safety.flags),
            )
        else:
            result = self._grounded_response(request, qualification.intent, qualification.score)

        if request.consent_to_store and self.repository is not None:
            try:
                self.repository.record(request.session_id, result)
                result.stored = True
            except RepositoryError:
                if self.metrics is not None:
                    self.metrics.record_storage_failure()
                raise

        if self.metrics is not None:
            self.metrics.record_response(
                intent=result.intent.value,
                action=result.recommended_action.value,
                generation_mode=result.generation_mode.value,
                requires_human=result.requires_human,
            )

        return result

    def _grounded_response(self, request: ChatRequest, intent: Intent, score: int) -> ChatResponse:
        matches = self.knowledge_base.search(request.message)
        if matches:
            answer = " ".join(entry.content for entry in matches)
            sources = [entry.title for entry in matches]
            generation_mode = GenerationMode.DETERMINISTIC
            if self.generator is not None:
                try:
                    answer = self.generator.rewrite(
                        user_message=request.message,
                        facts=tuple(entry.content for entry in matches),
                    )
                    generation_mode = GenerationMode.OLLAMA
                except GenerationError:
                    logger.warning("Model unavailable; using the grounded deterministic response")
                    generation_mode = GenerationMode.FALLBACK
            if intent is Intent.BOOKING:
                action = RecommendedAction.BOOK_CONSULTATION
                requires_human = False
            elif intent in {Intent.PRICING, Intent.CANCELLATION}:
                action = RecommendedAction.HUMAN_HANDOFF
                requires_human = True
            else:
                action = RecommendedAction.ANSWER
                requires_human = False
        elif intent in {Intent.PRICING, Intent.CANCELLATION}:
            answer = FALLBACK_RESPONSE
            sources = []
            generation_mode = GenerationMode.DETERMINISTIC
            action = RecommendedAction.HUMAN_HANDOFF
            requires_human = True
        elif intent is Intent.BOOKING:
            answer = (
                "I can help start a consultation request. Please share the service you are "
                "interested in, your preferred timeframe, and whether you prefer a call or text."
            )
            sources = []
            generation_mode = GenerationMode.DETERMINISTIC
            action = RecommendedAction.BOOK_CONSULTATION
            requires_human = False
        else:
            answer = FALLBACK_RESPONSE
            sources = []
            generation_mode = GenerationMode.DETERMINISTIC
            action = RecommendedAction.HUMAN_HANDOFF
            requires_human = True

        return ChatResponse(
            response=answer,
            intent=intent,
            qualification_score=score,
            recommended_action=action,
            requires_human=requires_human,
            knowledge_sources=sources,
            generation_mode=generation_mode,
        )
