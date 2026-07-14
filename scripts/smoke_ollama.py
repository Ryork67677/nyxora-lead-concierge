from __future__ import annotations

import json

from nyxora_concierge.generation import OllamaGenerator
from nyxora_concierge.knowledge import KnowledgeBase
from nyxora_concierge.models import ChatRequest, GenerationMode
from nyxora_concierge.service import ConciergeService


def main() -> int:
    service = ConciergeService(
        KnowledgeBase.from_package(),
        generator=OllamaGenerator(
            base_url="http://127.0.0.1:11434",
            model="qwen3:14b",
            timeout_seconds=90,
        ),
    )
    result = service.respond(
        ChatRequest(
            session_id="ollama-smoke-test",
            message="I am a first-time client. Can I book a consultation next week?",
        )
    )
    print(json.dumps(result.model_dump(mode="json"), indent=2))
    return 0 if result.generation_mode is GenerationMode.OLLAMA else 1


if __name__ == "__main__":
    raise SystemExit(main())

