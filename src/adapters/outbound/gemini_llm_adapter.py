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
        timeout: float = 300.0
    ):
        if timeout and timeout > 0:
            timeout_ms = max(10_000, int(timeout * 1000 if timeout < 1000 else timeout))
            self.client = genai.Client(api_key=api_key, http_options={"timeout": timeout_ms})
        else:
            self.client = genai.Client(api_key=api_key)
        self.state_repo = state_repo
        self.model = model
        self.daily_limit = daily_limit

    def get_remaining_calls(self) -> int:
        used = self.state_repo.get_daily_usage()
        return max(0, self.daily_limit - used)

    def _check_quota_available(self) -> None:
        used = self.state_repo.get_daily_usage()
        if used >= self.daily_limit:
            raise RuntimeError(
                f"Limite giornaliero Gemini raggiunto ({self.daily_limit} RPD). "
                "Riprova domani."
            )

    def _record_successful_call(self) -> None:
        new_count = self.state_repo.increment_daily_usage()
        remaining = max(0, self.daily_limit - new_count)
        print(f"    [Gemini] Chiamata {new_count}/{self.daily_limit} completata — rimaste oggi: {remaining}")

    def generate_notes(self, prompt: str, content_payload: Any) -> str:
        self._check_quota_available()

        # Sanitize text payload if string
        if isinstance(content_payload, str):
            content_payload = content_payload.replace("\x00", "").strip()
            if not content_payload:
                raise ValueError("Il contenuto estratto dal documento è vuoto.")

        # Candidate models for resilience: user-configured model first, then standard fallbacks
        candidate_models = [self.model]
        for fallback in ["gemini-2.0-flash", "gemini-1.5-flash"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        max_retries = 5
        base_delay = 15

        # Prepare contents list supporting single payload (str or File) or composite list
        contents_list = [prompt]
        if isinstance(content_payload, list):
            if not content_payload:
                raise ValueError("Il contenuto estratto dal documento è vuoto.")
            for item in content_payload:
                if isinstance(item, str):
                    sanitized = item.replace("\x00", "").strip()
                    if sanitized:
                        contents_list.append(sanitized)
                elif item is not None:
                    contents_list.append(item)
        else:
            contents_list.append(content_payload)

        for current_model in candidate_models:
            for attempt in range(max_retries):
                try:
                    response_stream = self.client.models.generate_content_stream(
                        model=current_model,
                        contents=contents_list,
                    )

                    full_text = ""
                    for chunk in response_stream:
                        try:
                            if chunk.text:
                                full_text += chunk.text
                        except Exception:
                            pass

                    full_text = full_text.strip()
                    if not full_text:
                        raise RuntimeError("Risposta ricevuta da Gemini vuota o filtrata dai filtri di sicurezza.")

                    if current_model != self.model:
                        print(f"    [Gemini Info] Inferenza completata con successo usando il modello fallback '{current_model}'.")
                        self.model = current_model

                    self._record_successful_call()
                    return full_text

                except Exception as exc:
                    exc_str = str(exc)

                    # 1. Quota exhaustion (fatal, do not retry)
                    if "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str:
                        raise RuntimeError(
                            f"Quota API esaurita (Errore 429). Elaborazione bloccata. Dettagli: {exc}"
                        )

                    # 2. Authentication failure (fatal, do not retry)
                    if "API_KEY_INVALID" in exc_str or "API key not valid" in exc_str:
                        raise RuntimeError(
                            f"Chiave GEMINI_API_KEY non valida (Errore 400/401). Verifica il file .env. Dettagli: {exc}"
                        )

                    # 3. Model not found or unsupported model -> attempt fallback candidate
                    is_model_error = (
                        "404" in exc_str
                        or "not found" in exc_str.lower()
                        or ("400" in exc_str and ("model" in exc_str.lower() or "not supported" in exc_str.lower()))
                    )
                    if is_model_error and current_model != candidate_models[-1]:
                        print(
                            f"    [Gemini Model Warning] Modello '{current_model}' non disponibile ({exc}). "
                            f"Tentativo con il modello successivo..."
                        )
                        break

                    # 4. Other client errors (400, 403, 404, INVALID_ARGUMENT) are deterministic -> fail fast, do NOT retry
                    is_client_error = (
                        "400" in exc_str
                        or "403" in exc_str
                        or "404" in exc_str
                        or "INVALID_ARGUMENT" in exc_str
                        or "PERMISSION_DENIED" in exc_str
                    )
                    if is_client_error:
                        raise RuntimeError(
                            f"Errore client API Gemini ({exc}). La richiesta non è valida o non supportata dal modello."
                        )

                    # 5. Only transient network or 5xx server errors get retried
                    if attempt == max_retries - 1:
                        raise exc

                    delay = base_delay * (2 ** attempt)
                    print(
                        f"    [ATTENZIONE] Rete/Server Google instabile ({exc}). "
                        f"Ritento tra {delay}s... ({attempt + 1}/{max_retries})"
                    )
                    time.sleep(delay)

        raise RuntimeError("Inference fallita dopo tutti i tentativi di retry e modelli alternativi.")
