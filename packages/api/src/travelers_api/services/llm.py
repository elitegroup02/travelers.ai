from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel

from ..core.config import get_settings


class POIData(BaseModel):
    """Input data for POI summary generation"""

    name: str
    year_built: int | None = None
    architect: str | None = None
    architectural_style: str | None = None
    heritage_status: str | None = None
    wikipedia_extract: str | None = None


class SummaryResult(BaseModel):
    """Generated summary in both languages"""

    summary_en: str
    summary_es: str


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    async def generate_summary(
        self, poi_data: POIData, language: Literal["en", "es"] = "en"
    ) -> str:
        """Generate a POI summary in the specified language"""
        pass

    async def generate_bilingual_summary(self, poi_data: POIData) -> SummaryResult:
        """Generate summaries in both English and Spanish"""
        summary_en = await self.generate_summary(poi_data, "en")
        summary_es = await self.generate_summary(poi_data, "es")
        return SummaryResult(summary_en=summary_en, summary_es=summary_es)

    def _build_prompt(self, poi_data: POIData, language: Literal["en", "es"]) -> str:
        """Build the prompt for summary generation"""
        # Build context from available data
        context_parts = []
        if poi_data.year_built:
            context_parts.append(f"Built: {poi_data.year_built}")
        if poi_data.architect:
            context_parts.append(f"Architect: {poi_data.architect}")
        if poi_data.architectural_style:
            context_parts.append(f"Style: {poi_data.architectural_style}")
        if poi_data.heritage_status:
            context_parts.append(f"Status: {poi_data.heritage_status}")

        context = "\n".join(context_parts) if context_parts else "Limited data available"
        extract = poi_data.wikipedia_extract or "No Wikipedia description available."

        lang_instruction = {
            "en": "Write the summary in English.",
            "es": "Escribe el resumen en español.",
        }

        return f"""You are a travel guide writer creating concise, memorable descriptions for tourists.

Given this information about "{poi_data.name}":

STRUCTURED DATA:
{context}

WIKIPEDIA EXTRACT:
{extract}

Write a 3-sentence summary (maximum 60 words total) that a tourist would find useful and memorable.

Requirements:
1. First sentence: Historical context or origin story
2. Second sentence: One visual/architectural highlight to look for when visiting
3. Third sentence: A practical tip, lesser-known fact, or what makes it special

Style guidelines:
- Engaging and conversational tone
- Avoid generic phrases like "must-see", "don't miss", "iconic"
- Include specific details that make the place unique
- If data is limited, focus on what IS known without apologizing for gaps

{lang_instruction[language]}

Respond with ONLY the 3-sentence summary, no additional text."""


class LlamaCppProvider(LLMProvider):
    """Local LLM inference using llama.cpp"""

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            try:
                from llama_cpp import Llama

                if not self.model_path:
                    raise ValueError("LLAMA_MODEL_PATH environment variable is required")
                self._llm = Llama(
                    model_path=self.model_path,
                    n_ctx=2048,
                    n_threads=4,
                )
            except ImportError:
                raise ImportError("llama-cpp-python is required for local inference")
        return self._llm

    async def generate_summary(
        self, poi_data: POIData, language: Literal["en", "es"] = "en"
    ) -> str:
        llm = self._get_llm()
        prompt = self._build_prompt(poi_data, language)

        output = llm(
            prompt,
            max_tokens=200,
            temperature=0.7,
            stop=["###", "\n\n\n"],
        )

        return output["choices"][0]["text"].strip()


class OpenAIProvider(LLMProvider):
    """OpenAI API provider"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI

                if not self.api_key:
                    raise ValueError("OPENAI_API_KEY environment variable is required")
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package is required for OpenAI provider")
        return self._client

    async def generate_summary(
        self, poi_data: POIData, language: Literal["en", "es"] = "en"
    ) -> str:
        client = self._get_client()
        prompt = self._build_prompt(poi_data, language)

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic

                if not self.api_key:
                    raise ValueError("ANTHROPIC_API_KEY environment variable is required")
                self._client = AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package is required for Anthropic provider")
        return self._client

    async def generate_summary(
        self, poi_data: POIData, language: Literal["en", "es"] = "en"
    ) -> str:
        client = self._get_client()
        prompt = self._build_prompt(poi_data, language)

        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text.strip()


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Factory function to get the configured LLM provider"""
    settings = get_settings()

    if settings.llm_provider == "llama":
        return LlamaCppProvider(model_path=settings.llama_model_path)
    elif settings.llm_provider == "openai":
        return OpenAIProvider(api_key=settings.openai_api_key)
    elif settings.llm_provider == "anthropic":
        return AnthropicProvider(api_key=settings.anthropic_api_key)
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
