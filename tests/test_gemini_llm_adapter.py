import pytest
from unittest.mock import MagicMock
from src.adapters.outbound.gemini_llm_adapter import GeminiLlmAdapter


@pytest.fixture
def mock_state_repo():
    repo = MagicMock()
    repo.get_daily_usage.return_value = 0
    repo.increment_daily_usage.return_value = 1
    return repo


@pytest.fixture
def mock_genai_client():
    client = MagicMock()
    return client


def test_gemini_llm_adapter_success_stream(mock_state_repo, mock_genai_client):
    chunk1 = MagicMock()
    chunk1.text = "Hello "
    chunk2 = MagicMock()
    chunk2.text = "World"
    mock_genai_client.models.generate_content_stream.return_value = [chunk1, chunk2]

    adapter = GeminiLlmAdapter(
        api_key="fake",
        state_repo=mock_state_repo,
        model="gemini-2.5-flash",
    )
    adapter.client = mock_genai_client

    result = adapter.generate_notes(prompt="test prompt", content_payload="test payload")

    assert result == "Hello World"
    mock_genai_client.models.generate_content_stream.assert_called_once_with(
        model="gemini-2.5-flash",
        contents=["test prompt", "test payload"],
    )


def test_gemini_llm_adapter_model_fallback_on_404(mock_state_repo, mock_genai_client):
    chunk = MagicMock()
    chunk.text = "Success on fallback"

    # First call with gemini-2.5-flash raises 404 model not found, second with gemini-2.0-flash succeeds
    def side_effect(model, contents):
        if model == "gemini-2.5-flash":
            raise Exception("404 Not Found: models/gemini-2.5-flash is not available")
        return [chunk]

    mock_genai_client.models.generate_content_stream.side_effect = side_effect

    adapter = GeminiLlmAdapter(
        api_key="fake",
        state_repo=mock_state_repo,
        model="gemini-2.5-flash",
    )
    adapter.client = mock_genai_client

    result = adapter.generate_notes(prompt="prompt", content_payload="payload")

    assert result == "Success on fallback"
    assert adapter.model == "gemini-2.0-flash"


def test_gemini_llm_adapter_fails_fast_on_client_error_400(mock_state_repo, mock_genai_client):
    mock_genai_client.models.generate_content_stream.side_effect = Exception(
        "400 INVALID_ARGUMENT: Unsupported parameter"
    )

    adapter = GeminiLlmAdapter(
        api_key="fake",
        state_repo=mock_state_repo,
        model="gemini-2.0-flash",
    )
    adapter.client = mock_genai_client

    with pytest.raises(RuntimeError, match="Errore client API Gemini"):
        adapter.generate_notes(prompt="prompt", content_payload="payload")

    # Should not retry 5 times on 400
    assert mock_genai_client.models.generate_content_stream.call_count <= 2


def test_gemini_llm_adapter_fails_fast_on_invalid_api_key(mock_state_repo, mock_genai_client):
    mock_genai_client.models.generate_content_stream.side_effect = Exception(
        "400 INVALID_ARGUMENT: API_KEY_INVALID. Please pass a valid API key."
    )

    adapter = GeminiLlmAdapter(
        api_key="fake",
        state_repo=mock_state_repo,
    )
    adapter.client = mock_genai_client

    with pytest.raises(RuntimeError, match="Chiave GEMINI_API_KEY non valida"):
        adapter.generate_notes(prompt="prompt", content_payload="payload")


def test_gemini_llm_adapter_fails_fast_on_429(mock_state_repo, mock_genai_client):
    mock_genai_client.models.generate_content_stream.side_effect = Exception(
        "429 RESOURCE_EXHAUSTED: Quota exceeded"
    )

    adapter = GeminiLlmAdapter(
        api_key="fake",
        state_repo=mock_state_repo,
    )
    adapter.client = mock_genai_client

    with pytest.raises(RuntimeError, match="Quota API esaurita"):
        adapter.generate_notes(prompt="prompt", content_payload="payload")


def test_gemini_llm_adapter_sanitizes_null_bytes(mock_state_repo, mock_genai_client):
    chunk = MagicMock()
    chunk.text = "Ok"
    mock_genai_client.models.generate_content_stream.return_value = [chunk]

    adapter = GeminiLlmAdapter(
        api_key="fake",
        state_repo=mock_state_repo,
    )
    adapter.client = mock_genai_client

    adapter.generate_notes(prompt="prompt", content_payload="text\x00with\x00null")

    call_args = mock_genai_client.models.generate_content_stream.call_args[1]
    assert call_args["contents"] == ["prompt", "textwithnull"]


def test_gemini_llm_adapter_timeout_converted_to_milliseconds(monkeypatch, mock_state_repo):
    captured_client_kwargs = {}

    class FakeClient:
        def __init__(self, **kwargs):
            captured_client_kwargs.update(kwargs)

    monkeypatch.setattr("google.genai.Client", FakeClient)

    adapter = GeminiLlmAdapter(api_key="test_key", state_repo=mock_state_repo, timeout=300.0)
    assert captured_client_kwargs["http_options"]["timeout"] == 300000

    # Minimum deadline clamp test
    adapter_low = GeminiLlmAdapter(api_key="test_key", state_repo=mock_state_repo, timeout=2.0)
    assert captured_client_kwargs["http_options"]["timeout"] == 10000


def test_gemini_llm_adapter_composite_list_payload(mock_state_repo, mock_genai_client):
    chunk = MagicMock()
    chunk.text = "Generated notes from multimodal"
    mock_genai_client.models.generate_content_stream.return_value = [chunk]

    adapter = GeminiLlmAdapter(
        api_key="fake",
        state_repo=mock_state_repo,
    )
    adapter.client = mock_genai_client

    mock_file = MagicMock()
    payload = ["Speaker notes text \x00sanitized", mock_file]

    result = adapter.generate_notes(prompt="System prompt", content_payload=payload)

    assert result == "Generated notes from multimodal"
    call_args = mock_genai_client.models.generate_content_stream.call_args[1]
    assert call_args["contents"] == ["System prompt", "Speaker notes text sanitized", mock_file]


def test_gemini_llm_adapter_empty_list_payload_raises(mock_state_repo, mock_genai_client):
    adapter = GeminiLlmAdapter(
        api_key="fake",
        state_repo=mock_state_repo,
    )
    adapter.client = mock_genai_client

    with pytest.raises(ValueError, match="vuoto"):
        adapter.generate_notes(prompt="System prompt", content_payload=[])


