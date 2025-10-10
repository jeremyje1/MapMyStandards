"""
Security validation utilities for MapMyStandards
Validates environment variables and detects potential security issues
"""

import os
import re
import sys
from typing import List, Tuple


class SecurityValidator:
    """Validates security configuration and detects potential issues"""

    # Patterns for secret detection
    SECRET_PATTERNS = [
        (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
        (r"sk-[a-zA-Z0-9]{20,}T3BlbkFJ[a-zA-Z0-9]{20,}", "OpenAI API Key"),
        (r"(sk|pk)_(test|live)_[0-9a-zA-Z]{24,}", "Stripe API Key"),
        (r"mlsn\.[a-zA-Z0-9]{20,}", "MailerSend API Key"),
        (r"SG\.[a-zA-Z0-9_\-]{22}\.[a-zA-Z0-9_\-]{43}", "SendGrid API Key"),
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Token"),
        (r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----", "Private Key"),
    ]

    # Required environment variables for production
    REQUIRED_ENV_VARS = [
        "SECRET_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "OPENAI_API_KEY",
    ]

    # Environment variables that should NOT be hardcoded
    SENSITIVE_ENV_VARS = [
        "SECRET_KEY",
        "POSTGRES_PASSWORD",
        "REDIS_PASSWORD",
        "MINIO_SECRET_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "OPENAI_API_KEY",
        "STRIPE_SECRET_KEY",
        "MAILERSEND_API_KEY",
        "SENDGRID_API_KEY",
    ]

    @staticmethod
    def check_required_env_vars() -> Tuple[bool, List[str]]:
        """Check if all required environment variables are set"""
        missing = []
        for var in SecurityValidator.REQUIRED_ENV_VARS:
            if not os.getenv(var):
                missing.append(var)

        return len(missing) == 0, missing

    @staticmethod
    def validate_secret_strength(secret: str, min_length: int = 32) -> Tuple[bool, str]:
        """Validate that a secret meets minimum security requirements"""
        if not secret:
            return False, "Secret is empty"

        if len(secret) < min_length:
            return False, f"Secret too short (minimum {min_length} characters)"

        # Check for common weak patterns
        weak_patterns = [
            "password",
            "12345",
            "admin",
            "secret",
            "qwerty",
            "test",
            "demo",
        ]

        secret_lower = secret.lower()
        for pattern in weak_patterns:
            if pattern in secret_lower:
                return False, f"Secret contains weak pattern: {pattern}"

        return True, "Secret meets security requirements"

    @staticmethod
    def scan_for_secrets(text: str) -> List[Tuple[str, str]]:
        """Scan text for potential secrets"""
        findings = []

        for pattern, secret_type in SecurityValidator.SECRET_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                findings.append((secret_type, match.group()))

        return findings

    @staticmethod
    def validate_environment() -> Tuple[bool, List[str]]:
        """Validate the entire environment configuration"""
        issues = []

        # Check required vars
        has_required, missing = SecurityValidator.check_required_env_vars()
        if not has_required:
            issues.append(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        # Check SECRET_KEY strength
        secret_key = os.getenv("SECRET_KEY")
        if secret_key:
            is_valid, message = SecurityValidator.validate_secret_strength(secret_key)
            if not is_valid:
                issues.append(f"SECRET_KEY issue: {message}")

        # Check for development mode in production
        environment = os.getenv("ENVIRONMENT", "development")
        debug = os.getenv("DEBUG", "false").lower() == "true"

        if environment == "production" and debug:
            issues.append("DEBUG mode is enabled in production environment")

        # Check CORS configuration
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
        if "*" in allowed_origins and environment == "production":
            issues.append("CORS allows all origins (*) in production")

        return len(issues) == 0, issues

    @staticmethod
    def check_file_for_secrets(filepath: str) -> List[Tuple[str, int, str]]:
        """Check a file for potential secrets"""
        findings = []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    secrets = SecurityValidator.scan_for_secrets(line)
                    for secret_type, secret_value in secrets:
                        findings.append(
                            (secret_type, line_num, secret_value[:20] + "...")
                        )
        except Exception as e:
            print(f"Error reading {filepath}: {e}", file=sys.stderr)

        return findings


def main():
    """Main validation function"""
    print("🔍 Running security validation...")
    print("=" * 60)

    # Validate environment
    is_valid, issues = SecurityValidator.validate_environment()

    if is_valid:
        print("✅ Environment validation passed")
    else:
        print("❌ Environment validation failed:")
        for issue in issues:
            print(f"   - {issue}")
        sys.exit(1)

    # Check for secrets in environment values
    print("\n🔍 Checking environment variables for exposed secrets...")
    exposed_secrets = []

    for key, value in os.environ.items():
        if key in SecurityValidator.SENSITIVE_ENV_VARS and value:
            secrets = SecurityValidator.scan_for_secrets(value)
            if secrets:
                exposed_secrets.append((key, secrets))

    if exposed_secrets:
        print("⚠️  Warning: Secrets detected in environment variables")
        for key, secrets in exposed_secrets:
            print(f"   - {key}: {len(secrets)} potential secret(s)")
    else:
        print("✅ No exposed secrets in environment variables")

    print("\n" + "=" * 60)
    print("✅ Security validation complete")


if __name__ == "__main__":
    main()
