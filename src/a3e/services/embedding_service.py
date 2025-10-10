"""Embedding utilities for EvidenceMapper pipeline."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Iterable, List

import httpx

from ..core.config import Settings

try:  # Optional Bedrock dependency
    import boto3  # type: ignore
except Exception:  # pragma: no cover
    boto3 = None  # type: ignore

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Provider-agnostic embedding helper supporting Bedrock Titan and OpenAI."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._openai_api_key = settings.openai_api_key
        self._openai_model = settings.openai_embed_model
        self._bedrock_model = settings.bedrock_model_embed
        self._bedrock_client = None

        if boto3 and settings.aws_access_key_id and settings.aws_secret_access_key:
            try:
                self._bedrock_client = boto3.client(
                    "bedrock-runtime",
                    region_name=settings.bedrock_region,
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                )
                logger.info("Bedrock embedding client initialized")
            except Exception as exc:  # pragma: no cover - network/cred errors
                logger.warning("Bedrock embedding client unavailable: %s", exc)

    async def embed(self, texts: Iterable[str]) -> List[List[float]]:
        payload = [self._truncate(text) for text in texts]
        if not payload:
            return []

        if self._bedrock_client is not None:
            return await asyncio.to_thread(self._embed_bedrock, payload)
        if self._openai_api_key:
            return await self._embed_openai(payload)
        raise RuntimeError("No embedding provider configured")

    # ------------------------------------------------------------------
    def _embed_bedrock(self, texts: List[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            body = json.dumps({"inputText": text})
            response = self._bedrock_client.invoke_model(  # type: ignore[union-attr]
                modelId=self._bedrock_model,
                body=body,
                contentType="application/json",
                accept="application/json",
            )
            payload = json.loads(response["body"].read())
            vector = payload.get("embedding") or payload.get("vector")
            if vector is None:
                raise RuntimeError("Bedrock response missing embedding vector")
            vectors.append([float(x) for x in vector])
        return vectors

    async def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        headers = {
            "Authorization": f"Bearer {self._openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self._openai_model, "input": texts}
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post("https://api.openai.com/v1/embeddings", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        vectors = []
        for item in data.get("data", []):
            vector = item.get("embedding")
            if vector is None:
                raise RuntimeError("OpenAI embedding missing vector")
            vectors.append([float(x) for x in vector])
        return vectors

    @staticmethod
    def _truncate(text: str, max_chars: int = 4000) -> str:
        text = text or ""
        return text[:max_chars]
