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

# Optional AWS imports
try:  # Optional AWS
    import boto3  # type: ignore
    from botocore.exceptions import ClientError  # type: ignore
    AWS_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    AWS_AVAILABLE = False
    
    class ClientError(Exception):  # type: ignore
        pass

# Optional AI service imports (should be available in minimal requirements)
try:  # Optional AI services
    import openai  # type: ignore
    import anthropic  # type: ignore
    AI_SERVICES_AVAILABLE = True
except ImportError:  # pragma: no cover
    AI_SERVICES_AVAILABLE = False

from ..core.config import Settings

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
        self.anthropic_client = None
        
    async def initialize(self):
        """Initialize LLM clients"""
        try:
            # Initialize AWS Bedrock client
            if self.settings.aws_access_key_id and self.settings.aws_secret_access_key:
                self.bedrock_client = boto3.client(
                    'bedrock-runtime',
                    region_name=self.settings.bedrock_region,
                    aws_access_key_id=self.settings.aws_access_key_id,
                    aws_secret_access_key=self.settings.aws_secret_access_key
                )
                logger.info("✅ AWS Bedrock client initialized")
            
            # Initialize OpenAI client
            if self.settings.openai_api_key:
                self.openai_client = openai.AsyncOpenAI(
                    api_key=self.settings.openai_api_key
                )
                logger.info("✅ OpenAI client initialized")
            
            # Initialize Anthropic client
            if self.settings.anthropic_api_key:
                self.anthropic_client = anthropic.AsyncAnthropic(
                    api_key=self.settings.anthropic_api_key
                )
                logger.info("✅ Anthropic client initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize LLM clients: {e}")
            raise
    
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
            elif self.openai_client and "gpt" in model.lower():
                return await self._generate_openai_response(
                    prompt, model, temperature, max_tokens, agent_name
                )
            
            # Fallback to Anthropic direct API
            elif self.anthropic_client and "claude" in model.lower():
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
        """Generate response using OpenAI"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are the {agent_name} agent in the A3E accreditation system."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            usage = response.usage
            
            # Estimate cost for OpenAI models
            cost_estimate = self._calculate_openai_cost(
                model,
                usage.prompt_tokens,
                usage.completion_tokens
            )
            
            return LLMResponse(
                content=content,
                model=model,
                usage={
                    'prompt_tokens': usage.prompt_tokens,
                    'completion_tokens': usage.completion_tokens,
                    'total_tokens': usage.total_tokens
                },
                finish_reason=response.choices[0].finish_reason,
                cost_estimate=cost_estimate
            )
            
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise
    
    async def _generate_anthropic_response(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        agent_name: str
    ) -> LLMResponse:
        """Generate response using Anthropic direct API"""
        
        try:
            # New SDK (0.39.0+) - messages is always available for AsyncAnthropic
            response = await self.anthropic_client.messages.create(
                model=model.replace("anthropic.", "").replace(":0", ""),  # Clean up model name
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            content = response.content[0].text
            usage = response.usage
            
            # Estimate cost for Anthropic models
            cost_estimate = self._calculate_anthropic_cost(
                model,
                usage.input_tokens,
                usage.output_tokens
            )
            
            return LLMResponse(
                content=content,
                model=model,
                usage={
                    'prompt_tokens': usage.input_tokens,
                    'completion_tokens': usage.output_tokens,
                    'total_tokens': usage.input_tokens + usage.output_tokens
                },
                finish_reason=response.stop_reason,
                cost_estimate=cost_estimate
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
