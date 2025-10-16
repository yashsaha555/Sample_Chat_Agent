import os
from typing import Optional


class LLMClient:
    async def chat(self, content: str, system: Optional[str] = None) -> str:
        raise NotImplementedError


class OpenAIClient(LLMClient):
    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async def chat(self, content: str, system: Optional[str] = None) -> str:
        sys = system or "You are a helpful assistant."
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": content},
            ],
        )
        return resp.choices[0].message.content


class OllamaClient(LLMClient):
    def __init__(self):
        import ollama
        self.ollama = ollama
        self.model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    async def chat(self, content: str, system: Optional[str] = None) -> str:
        # Ollama python client is sync; call in threadpool if needed. For hackathon, call directly.
        sys = system or "You are a helpful assistant."
        r = self.ollama.chat(model=self.model, messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": content},
        ])
        return r.get("message", {}).get("content", "")


def get_llm_client() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider in ("openai", "deepseek", "azureopenai"):
        return OpenAIClient()
    if provider == "ollama":
        return OllamaClient()
    return OpenAIClient()
