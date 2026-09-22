import time
import google.genai as genai
from typing import Any
from src.ports.outbound.llm_client_port import ILlmClient
from src.ports.outbound.state_repository_port import IStateRepository

class GeminiLlmAdapter(ILlmClient):
    """
    Adapter for Google Gemini API via google-genai SDK.
    Enforces daily quota safety limits and exponential backoff retry for resilient inference.
    """
    def __init__(
        self,
        api_key: str,
        state_repo: IStateRepository,
        model: str = "gemini-2.5-flash",
        daily_limit: int = 20,
        timeout: float = 20.0
    ):
        self.client = genai.Client(api_key=api_key, http_options={"timeout": timeout})
        self.state_repo = state_repo
        self.model = model
        self.daily_limit = daily_limit

    def get_remaining_calls(self) -> int:
        used = self.state_repo.get_daily_usage()
        return max(0, self.daily_limit - used)

    def _check_and_increment_quota(self) -> None:
        used = self.state_repo.get_daily_usage()
        if used >= self.daily_limit:
            raise RuntimeError(
                f"Limite giornaliero Gemini raggiunto ({self.daily_limit} RPD). "
                "Riprova domani."
            )
        new_count = self.state_repo.increment_daily_usage()
        remaining = max(0, self.daily_limit - new_count)
        print(f"    [Gemini] Chiamata {new_count}/{self.daily_limit} — rimaste oggi: {remaining}")

    def generate_notes(self, prompt: str, content_payload: Any) -> str:
        self._check_and_increment_quota()

        max_retries = 5
        base_delay = 15

        for attempt in range(max_retries):
            try:
                response_stream = self.client.models.generate_content_stream(
                    model=self.model,
                    contents=[prompt, content_payload],
                )

                full_text = ""
                for chunk in response_stream:
                    if chunk.text:
                        full_text += chunk.text

                return full_text

            except Exception as exc:
                if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                    raise RuntimeError(
                        f"Quota API esaurita (Errore 429). Elaborazione bloccata. Dettagli: {exc}"
                    )

                if attempt == max_retries - 1:
                    raise exc

                delay = base_delay * (2 ** attempt)
                print(
                    f"    [ATTENZIONE] Rete/Server instabile ({exc}). "
                    f"Ritento tra {delay}s... ({attempt + 1}/{max_retries})"
                )
                time.sleep(delay)

        raise RuntimeError("Inference fallita dopo tutti i tentativi di retry.")
