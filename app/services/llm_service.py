"""Turns a free-form trip description into origin + destinations using an LLM."""
import json
import logging
from functools import lru_cache
from typing import Optional

import openai
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError, field_validator

from app.config import get_settings
from app.errors import RouteError, UpstreamError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You extract trip plans from short messages. The message can be in any language (usually Spanish).

Return a JSON object with exactly these keys:
- "origin": string or null. Where the trip starts.
- "destinations": array of strings. Every place the person wants to visit, in the order mentioned.
- "return_to_origin": boolean. True only if they say they come back to the start (for example "volver", "regresar", "back home", "return to the office").

Rules:
- Copy each place exactly as written, keeping street numbers, district and city ("Av. Larco 789, Miraflores"). Fix obvious typos only.
- If a place has a street address and a district mentioned separately, join them into one string.
- Never invent places and never add a country.
- If no explicit starting point is given, use the first place mentioned as the origin.
- Do not repeat the origin inside "destinations", even when they return to it.
- If the message is not about visiting places, return {"origin": null, "destinations": [], "return_to_origin": false}."""


class ParsedRoute(BaseModel):
    origin: Optional[str] = None
    destinations: list[str] = Field(default_factory=list)
    return_to_origin: bool = False

    @field_validator("destinations", mode="before")
    @classmethod
    def _drop_non_strings(cls, value):
        if not isinstance(value, list):
            return []
        return [v for v in value if isinstance(v, str) and v.strip()]

    @field_validator("origin", mode="before")
    @classmethod
    def _blank_origin_to_none(cls, value):
        if not isinstance(value, str) or not value.strip():
            return None
        return value


@lru_cache
def _client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.llm_timeout_seconds,
        max_retries=2,
    )


class LLMService:
    def __init__(self, client: Optional[OpenAI] = None):
        self.settings = get_settings()
        self.client = client or _client()

    def parse_route_input(self, user_input: str) -> ParsedRoute:
        try:
            response = self.client.chat.completions.create(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"<message>\n{user_input}\n</message>"},
                ],
            )
        except openai.AuthenticationError as exc:
            logger.error("OpenAI rejected the API key: %s", exc)
            raise UpstreamError("The language model rejected the configured API key.") from exc
        except openai.RateLimitError as exc:
            raise UpstreamError("The language model is rate limited. Try again in a minute.") from exc
        except openai.OpenAIError as exc:
            logger.exception("OpenAI request failed")
            raise UpstreamError("Could not reach the language model.") from exc

        content = response.choices[0].message.content or "{}"
        try:
            return ParsedRoute.model_validate(json.loads(content))
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning("Unparseable LLM output: %r", content)
            raise RouteError("Could not understand the trip description. Try listing the places more explicitly.") from exc
