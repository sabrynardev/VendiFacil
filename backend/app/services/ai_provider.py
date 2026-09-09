from typing import Protocol


class AIProvider(Protocol):
    def respond(self, system_prompt: str, payload: dict) -> str:
        """Turn already aggregated, permission-filtered data into a short answer."""


class DisabledAIProvider:
    name = "disabled"

    def respond(self, system_prompt: str, payload: dict) -> str:
        raise RuntimeError("Assistente generativo não configurado neste ambiente.")


SYSTEM_PROMPT = """Você é o assistente do Vendi. Responda somente com os dados agregados
fornecidos pelas ferramentas. Nunca invente valores ou causas, sempre informe o período,
respeite permissões e não execute ações. Indicadores são gerenciais, não contábeis oficiais."""
