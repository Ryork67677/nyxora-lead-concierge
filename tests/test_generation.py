import json
from io import BytesIO
from unittest.mock import patch
from urllib.error import URLError

import pytest

from nyxora_concierge.generation import GenerationError, OllamaGenerator


class FakeHTTPResponse(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def test_ollama_generator_returns_message_content() -> None:
    response = FakeHTTPResponse(
        json.dumps({"message": {"content": " A grounded response. "}}).encode()
    )
    generator = OllamaGenerator("http://127.0.0.1:11434", "qwen3:14b")
    with patch("nyxora_concierge.generation.urlopen", return_value=response) as mocked:
        result = generator.rewrite(user_message="Hello", facts=("Verified fact.",))
    assert result == "A grounded response."
    request = mocked.call_args.args[0]
    payload = json.loads(request.data)
    assert payload["stream"] is False
    assert payload["think"] is False
    assert payload["model"] == "qwen3:14b"


def test_ollama_generator_wraps_transport_errors() -> None:
    generator = OllamaGenerator("http://127.0.0.1:11434", "qwen3:14b")
    with (
        patch("nyxora_concierge.generation.urlopen", side_effect=URLError("offline")),
        pytest.raises(GenerationError),
    ):
        generator.rewrite(user_message="Hello", facts=("Verified fact.",))


def test_ollama_generator_rejects_empty_content() -> None:
    response = FakeHTTPResponse(json.dumps({"message": {"content": ""}}).encode())
    generator = OllamaGenerator("http://127.0.0.1:11434", "qwen3:14b")
    with (
        patch("nyxora_concierge.generation.urlopen", return_value=response),
        pytest.raises(GenerationError),
    ):
        generator.rewrite(user_message="Hello", facts=("Verified fact.",))

