#!/usr/bin/env python3
"""
ShadowScribe Cloud Run Deployment Script

Deploys the API to Google Cloud Run with all necessary configuration.
Run with: python scripts/deploy_cloudrun.py
"""

import subprocess
import sys
from pathlib import Path

# ============ CONFIGURATION ============
PROJECT_ID = "shadowscribe-prod"
REGION = "us-central1"
SERVICE_NAME = "shadowscribe-api"

# Resource allocation
MEMORY = "2Gi"
CPU = "2"
TIMEOUT = "300"

# Secrets (from Google Secret Manager) - as environment variables
SECRETS = {
    "OPENAI_API_KEY": "openai-api-key:latest",
    "ANTHROPIC_API_KEY": "anthropic-api-key:latest",
}

# Secrets mounted as files (path=secret:version)
FILE_SECRETS = {
    "/secrets/firebase-service-account.json": "firebase-service-account:latest",
}

# Environment variables
# CORS origins - add your domains here
CORS_ORIGINS = [
    "https://shadow-scribe-six.vercel.app",
    "https://shadow-scribe-git-main-sherman-portfolios.vercel.app",
    "https://shadow-scribe-q9qe9p6ig-sherman-portfolios.vercel.app",
    "https://shadow-scribe-sherman-portfolios.vercel.app",
    "http://localhost:3000",
]

# ============ END CONFIGURATION ============


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def main():
    # Get project root (parent of scripts/)
    project_root = Path(__file__).parent.parent.absolute()
    
    print(f"🚀 Deploying ShadowScribe API to Cloud Run")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Region: {REGION}")
    print(f"   Service: {SERVICE_NAME}")
    print()

    # Verify gcloud is configured
    result = run_command(["gcloud", "config", "get-value", "project"], check=False)
    current_project = result.stdout.strip()
    if current_project != PROJECT_ID:
        print(f"⚠️  Current project is '{current_project}', switching to '{PROJECT_ID}'")
        run_command(["gcloud", "config", "set", "project", PROJECT_ID])

    # Build the deploy command
    cmd = [
        "gcloud", "run", "deploy", SERVICE_NAME,
        f"--region={REGION}",
        f"--source={project_root}",
        "--allow-unauthenticated",
        f"--memory={MEMORY}",
        f"--cpu={CPU}",
        f"--timeout={TIMEOUT}",
    ]

    # Add secrets as environment variables
    secrets_str = ",".join(f"{k}={v}" for k, v in SECRETS.items())
    # Add file-mounted secrets
    file_secrets_str = ",".join(f"{path}={secret}" for path, secret in FILE_SECRETS.items())
    all_secrets = f"{secrets_str},{file_secrets_str}"
    cmd.append(f"--set-secrets={all_secrets}")

    # Add environment variables (use ^@^ delimiter for values with commas)
    cors_str = ",".join(CORS_ORIGINS)
    # GOOGLE_APPLICATION_CREDENTIALS points to the mounted Firebase service account
    cmd.append(f"--set-env-vars=^@^CORS_ORIGINS={cors_str}@GOOGLE_APPLICATION_CREDENTIALS=/secrets/firebase-service-account.json")

    # Run deployment
    print("📦 Building and deploying...")
    print()
    
    # Run interactively so user can see progress
    subprocess.run(cmd, cwd=project_root)


if __name__ == "__main__":
    main()
