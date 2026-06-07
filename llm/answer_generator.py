import json
from typing import Optional
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from config import CHAT_MODEL, GOOGLE_API_KEY
from llm.prompts import ANSWER_PROMPT
from models.analysis import AnswerAnalysis

class RateLimitError(Exception):
    pass

_SCHEMA = AnswerAnalysis.model_json_schema()

class AnswerGenerator:
    """Generates a grounded answer and full analysis in a single LLM call."""

    def _build_prompt(self, question: str, history: str, context: str) -> str:
        return ANSWER_PROMPT.format(question=question, history=history, context=context)

    def generate(self, question: str, history: str, context: str, api_key: Optional[str] = None) -> AnswerAnalysis:
        """Generate answer, citations, conflict detection and analysis together."""
        key = api_key or GOOGLE_API_KEY
        client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=30000))
        prompt = self._build_prompt(question=question, history=history, context=context)

        try:
            response = client.models.generate_content(
                model=CHAT_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=_SCHEMA,
                    temperature=0,
                ),
            )
            data = json.loads(response.text)
            return AnswerAnalysis(**data)
        except ClientError as e:
            if e.status_code == 429:
                raise RateLimitError(str(e)) from e
            raise
