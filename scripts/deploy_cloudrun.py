#!/usr/bin/env python3
"""
ShadowScribe Cloud Run Deployment Script

Deploys the API to Google Cloud Run with all necessary configuration.

Usage:
    uv run python scripts/deploy_cloudrun.py              # Deploy with Cloud Build (default)
    uv run python scripts/deploy_cloudrun.py --local      # Build locally + push (faster!)
    uv run python scripts/deploy_cloudrun.py --patch      # Bump patch version (1.0.0 -> 1.0.1)
    uv run python scripts/deploy_cloudrun.py --minor      # Bump minor version (1.0.0 -> 1.1.0)
    uv run python scripts/deploy_cloudrun.py --major      # Bump major version (1.0.0 -> 2.0.0)
    uv run python scripts/deploy_cloudrun.py --version    # Show current version only

Local build is faster because:
    - Uses local Docker cache (no re-downloading layers)
    - Skips Cloud Build upload/queue time
    - Only pushes changed layers to Artifact Registry
"""

import argparse
import re
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

# Artifact Registry for local builds
ARTIFACT_REGISTRY = f"{REGION}-docker.pkg.dev"
REPOSITORY = "shadowscribe"
IMAGE_NAME = "api"

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


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.absolute()


def get_current_version() -> str:
    """Read the current version from pyproject.toml."""
    pyproject_path = get_project_root() / "pyproject.toml"
    content = pyproject_path.read_text()
    match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    if not match:
        print("Error: Could not find version in pyproject.toml")
        sys.exit(1)
    return match.group(1)


def bump_version(current: str, bump_type: str) -> str:
    """Bump version according to semver rules."""
    parts = current.split('.')
    if len(parts) != 3:
        print(f"Error: Invalid version format '{current}'. Expected X.Y.Z")
        sys.exit(1)
    
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        return current


def update_version_in_pyproject(new_version: str) -> None:
    """Update the version in pyproject.toml."""
    pyproject_path = get_project_root() / "pyproject.toml"
    content = pyproject_path.read_text()
    updated = re.sub(
        r'^(version\s*=\s*["\'])([^"\']+)(["\'])',
        f'\\g<1>{new_version}\\g<3>',
        content,
        flags=re.MULTILINE
    )
    pyproject_path.write_text(updated)


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Deploy ShadowScribe API to Google Cloud Run",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Version bump types:
  --patch    Bug fixes, small changes (1.0.0 -> 1.0.1)
  --minor    New features, backward compatible (1.0.0 -> 1.1.0)
  --major    Breaking changes (1.0.0 -> 2.0.0)
"""
    )
    version_group = parser.add_mutually_exclusive_group()
    version_group.add_argument('--patch', action='store_true', help='Bump patch version')
    version_group.add_argument('--minor', action='store_true', help='Bump minor version')
    version_group.add_argument('--major', action='store_true', help='Bump major version')
    version_group.add_argument('--version', action='store_true', help='Show current version and exit')
    parser.add_argument('--no-deploy', action='store_true', help='Only update version, skip deployment')
    parser.add_argument('--local', action='store_true', help='Build locally and push to Artifact Registry (faster)')
    return parser.parse_args()


def main():
    args = parse_args()
    project_root = get_project_root()
    
    # Get current version
    current_version = get_current_version()
    
    # Handle --version flag
    if args.version:
        print(f"ShadowScribe v{current_version}")
        return
    
    # Determine version bump
    bump_type = None
    if args.patch:
        bump_type = "patch"
    elif args.minor:
        bump_type = "minor"
    elif args.major:
        bump_type = "major"
    
    # Bump version if requested
    new_version = current_version
    if bump_type:
        new_version = bump_version(current_version, bump_type)
        print(f"📦 Bumping version: {current_version} -> {new_version}")
        update_version_in_pyproject(new_version)
        
        # Commit the version bump
        run_command(["git", "add", "pyproject.toml"], check=False)
        run_command(["git", "commit", "-m", f"chore: bump version to {new_version}"], check=False)
        print()
    
    if args.no_deploy:
        print(f"✅ Version updated to {new_version}. Skipping deployment.")
        return

    print(f"🚀 Deploying ShadowScribe API v{new_version} to Cloud Run")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Region: {REGION}")
    print(f"   Service: {SERVICE_NAME}")
    print(f"   Build: {'Local Docker' if args.local else 'Cloud Build'}")
    print()

    # Verify gcloud is configured
    result = run_command(["gcloud", "config", "get-value", "project"], check=False)
    current_project = result.stdout.strip()
    if current_project != PROJECT_ID:
        print(f"⚠️  Current project is '{current_project}', switching to '{PROJECT_ID}'")
        run_command(["gcloud", "config", "set", "project", PROJECT_ID])

    # Full image URL for Artifact Registry
    image_url = f"{ARTIFACT_REGISTRY}/{PROJECT_ID}/{REPOSITORY}/{IMAGE_NAME}:latest"
    
    # Local build path: build locally, push to Artifact Registry, deploy from image
    if args.local:
        print("📦 Building Docker image locally...")
        
        # Configure Docker for Artifact Registry
        run_command(["gcloud", "auth", "configure-docker", ARTIFACT_REGISTRY, "--quiet"])
        
        # Build locally for AMD64 (Cloud Run requires linux/amd64)
        run_command([
            "docker", "build",
            "--platform", "linux/amd64",
            "-t", image_url,
            "-f", "Dockerfile",
            str(project_root)
        ])
        
        print("\n📤 Pushing to Artifact Registry...")
        run_command(["docker", "push", image_url])
        
        print("\n🚀 Deploying from image...")
    else:
        print("📦 Building with Cloud Build...")

    # Build the deploy command
    cmd = [
        "gcloud", "run", "deploy", SERVICE_NAME,
        f"--region={REGION}",
        "--allow-unauthenticated",
        f"--memory={MEMORY}",
        f"--cpu={CPU}",
        f"--timeout={TIMEOUT}",
    ]
    
    # Use image URL for local builds, source for Cloud Build
    if args.local:
        cmd.append(f"--image={image_url}")
    else:
        cmd.append(f"--source={project_root}")

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
