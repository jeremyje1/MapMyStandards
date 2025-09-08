"""
LLM Service for A3E

Provides unified interface to various LLM providers including AWS Bedrock,
OpenAI, and Anthropic for the agent workflows.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import os

import httpx
from ..core.config import Settings

# Optional AWS imports
try:  # Optional AWS
    import boto3  # type: ignore
    from botocore.exceptions import ClientError  # type: ignore
    AWS_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    AWS_AVAILABLE = False
    
    class ClientError(Exception):  # type: ignore
        pass

# Avoid Anthropic SDK to prevent httpx wrapper issues; we'll call HTTP API directly
AI_SERVICES_AVAILABLE = True

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Standardized LLM response format"""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    cost_estimate: Optional[float] = None


class LLMService:
    """Unified LLM service supporting multiple providers"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.bedrock_client = None
        self.openai_client = None
        self.anthropic_client = None  # Deprecated path; keep attribute to avoid ref churn
        # OpenAI HTTP fallback state
        self._openai_http_fallback = False
        self._openai_api_key = None
        
    async def initialize(self):
        """Initialize LLM clients. Never crash app if a provider fails; degrade gracefully."""
        # Initialize AWS Bedrock client (optional)
        try:
            if self.settings.aws_access_key_id and self.settings.aws_secret_access_key:
                self.bedrock_client = boto3.client(
                    'bedrock-runtime',
                    region_name=self.settings.bedrock_region,
                    aws_access_key_id=self.settings.aws_access_key_id,
                    aws_secret_access_key=self.settings.aws_secret_access_key
                )
                logger.info("✅ AWS Bedrock client initialized")
        except Exception as e:
            logger.warning(f"AWS Bedrock initialization skipped: {e}")

        # Initialize OpenAI via HTTP fallback only (avoid SDK proxies bugs in this env)
        try:
            if self.settings.openai_api_key:
                self._openai_http_fallback = True
                self._openai_api_key = self.settings.openai_api_key
                logger.info("✅ OpenAI HTTP fallback enabled")
        except Exception as e:
            logger.warning(f"OpenAI initialization skipped: {e}")

        # Anthropic: indicate availability if key present; we'll use HTTPX instead of SDK
        if self.settings.anthropic_api_key:
            logger.info("✅ Anthropic HTTP enabled")
    
    async def generate_response(
        self,
        prompt: str,
        agent_name: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Generate response using the appropriate LLM provider"""
        
        model = model or self.settings.bedrock_model_id
        temperature = temperature or self.settings.agent_temperature
        max_tokens = max_tokens or self.settings.bedrock_max_tokens
        
        try:
            # Use AWS Bedrock as primary provider
            if self.bedrock_client and "claude" in model.lower():
                return await self._generate_bedrock_response(
                    prompt, model, temperature, max_tokens, agent_name
                )
            
            # Fallback to OpenAI
            elif (self._openai_http_fallback) and "gpt" in model.lower():
                return await self._generate_openai_response(
                    prompt, model, temperature, max_tokens, agent_name
                )
            
            # Fallback to Anthropic direct API
            elif self.settings.anthropic_api_key and "claude" in model.lower():
                return await self._generate_anthropic_response(
                    prompt, model, temperature, max_tokens, agent_name
                )
            
            else:
                raise ValueError(f"No suitable LLM provider available for model: {model}")
                
        except Exception as e:
            logger.error(f"LLM generation failed for {agent_name}: {e}")
            raise
    
    async def _generate_bedrock_response(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        agent_name: str
    ) -> LLMResponse:
        """Generate response using AWS Bedrock"""
        
        # Prepare the request body for Claude models
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId=model,
                body=json.dumps(body),
                contentType="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            
            content = response_body.get('content', [{}])[0].get('text', '')
            usage = response_body.get('usage', {})
            
            # Estimate cost for Claude models (approximate)
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            cost_estimate = self._calculate_bedrock_cost(model, input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                model=model,
                usage={
                    'prompt_tokens': input_tokens,
                    'completion_tokens': output_tokens,
                    'total_tokens': input_tokens + output_tokens
                },
                finish_reason=response_body.get('stop_reason'),
                cost_estimate=cost_estimate
            )
            
        except ClientError as e:
            logger.error(f"AWS Bedrock error: {e}")
            raise
    
    async def _generate_openai_response(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        agent_name: str
    ) -> LLMResponse:
        """Generate response using OpenAI (HTTP-only)."""
        try:
            if self._openai_http_fallback and self._openai_api_key:
                return await self._generate_openai_response_via_httpx(
                    prompt, model, temperature, max_tokens, agent_name
                )
            raise RuntimeError("OpenAI not configured")
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise

    async def _generate_openai_response_via_httpx(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        agent_name: str
    ) -> LLMResponse:
        """Direct HTTP fallback for OpenAI Chat Completions to avoid SDK issues."""
        headers = {
            "Authorization": f"Bearer {self._openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": f"You are the {agent_name} agent in the A3E accreditation system."},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            cost_estimate = self._calculate_openai_cost(model, prompt_tokens, completion_tokens)
            return LLMResponse(
                content=content,
                model=model,
                usage={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
                finish_reason=data["choices"][0].get("finish_reason"),
                cost_estimate=cost_estimate,
            )
    
    async def _generate_anthropic_response(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        agent_name: str
    ) -> LLMResponse:
        """Generate response using Anthropic via HTTP API"""
        try:
            headers = {
                "x-api-key": self.settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            # Normalize model name if prefixed
            model_name = model.replace("anthropic.", "").replace(":0", "")
            payload = {
                "model": model_name,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                content_items = data.get("content", [])
                content = content_items[0].get("text", "") if content_items else ""
                usage = data.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)

            cost_estimate = self._calculate_anthropic_cost(model, input_tokens, output_tokens)
            return LLMResponse(
                content=content,
                model=model,
                usage={
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                },
                finish_reason=data.get("stop_reason"),
                cost_estimate=cost_estimate,
            )
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            raise
    
    def _calculate_bedrock_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost for Bedrock models"""
        # Approximate pricing for Claude 3 Sonnet (as of 2025)
        if "claude-3-sonnet" in model:
            input_cost = input_tokens * 0.003 / 1000  # $3 per 1K input tokens
            output_cost = output_tokens * 0.015 / 1000  # $15 per 1K output tokens
            return input_cost + output_cost
        return 0.0
    
    def _calculate_openai_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost for OpenAI models"""
        # Approximate pricing for GPT-4 (as of 2025)
        if "gpt-4" in model:
            input_cost = input_tokens * 0.03 / 1000  # $30 per 1K input tokens
            output_cost = output_tokens * 0.06 / 1000  # $60 per 1K output tokens
            return input_cost + output_cost
        return 0.0
    
    def _calculate_anthropic_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost for Anthropic models"""
        # Approximate pricing for Claude 3 (as of 2025)
        if "claude-3" in model:
            input_cost = input_tokens * 0.003 / 1000  # $3 per 1K input tokens
            output_cost = output_tokens * 0.015 / 1000  # $15 per 1K output tokens
            return input_cost + output_cost
        return 0.0
    
    async def health_check(self) -> bool:
        """Check if LLM service is healthy"""
        try:
            # In development without real API keys, just check service availability
            if not self.settings.openai_api_key and not self.settings.anthropic_api_key:
                logger.info("LLM health check: No API keys configured - development mode OK")
                return True
                
            # Test with a simple prompt if we have API keys
            test_prompt = "Respond with 'OK' if you can hear me."
            response = await self.generate_response(
                test_prompt,
                "health_check",
                max_tokens=10
            )
            return "OK" in response.content.upper()
        except Exception as e:
            # In development mode, be more lenient with LLM failures
            if self.settings.environment == "development":
                logger.warning(f"LLM health check failed in development mode: {e}")
                return True
            logger.error(f"LLM health check failed: {e}")
            return False
