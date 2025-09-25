#!/usr/bin/env python3
"""Check valid AWS Bedrock model IDs"""

# Valid AWS Bedrock Anthropic Claude model IDs as of 2025
print("Valid AWS Bedrock Anthropic Claude Model IDs:")
print("=" * 60)

valid_models = [
    # Claude 3.5 Sonnet (most capable)
    "anthropic.claude-3-5-sonnet-20240620-v1:0",  # Original Claude 3.5 Sonnet
    "anthropic.claude-3-5-sonnet-20241022-v2:0",  # Latest Claude 3.5 Sonnet (October 2024)
    
    # Claude 3 Opus (previous most capable)
    "anthropic.claude-3-opus-20240229-v1:0",
    
    # Claude 3 Sonnet (balanced)
    "anthropic.claude-3-sonnet-20240229-v1:0",
    
    # Claude 3 Haiku (fastest, most cost-effective)
    "anthropic.claude-3-haiku-20240307-v1:0",
    
    # Claude 2.1 (legacy)
    "anthropic.claude-v2:1",
    "anthropic.claude-v2",
    
    # Claude Instant (legacy, fast)
    "anthropic.claude-instant-v1",
]

print("\nRecommended for production use:")
print("  - anthropic.claude-3-5-sonnet-20240620-v1:0  (Most capable, higher cost)")
print("  - anthropic.claude-3-sonnet-20240229-v1:0    (Balanced performance/cost)")
print("  - anthropic.claude-3-haiku-20240307-v1:0     (Fast, cost-effective)")

print("\n" + "=" * 60)
print("Current invalid model ID in Railway:")
print("  anthropic.claude-3-5-sonnet-20241022")
print("\nThis should be updated to one of:")
print("  - anthropic.claude-3-5-sonnet-20241022-v2:0  (if October 2024 version exists)")
print("  - anthropic.claude-3-5-sonnet-20240620-v1:0  (stable version)")

print("\nNote: Model availability may vary by AWS region.")