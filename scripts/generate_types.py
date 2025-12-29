#!/usr/bin/env python3
"""Generate TypeScript types from Pydantic models.

This script generates TypeScript type definitions from Python Pydantic models,
establishing Python as the single source of truth for type definitions.

Usage:
    uv run python scripts/generate_types.py

Requirements:
    - pydantic-to-typescript (Python package, installed via uv)
    - json-schema-to-typescript (npm package, installed in frontend/)

The script outputs to frontend/lib/types/generated/ and creates an index.ts
barrel export for easy importing.
"""
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
GENERATED_DIR = PROJECT_ROOT / "frontend" / "lib" / "types" / "generated"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# (module_path, output_filename)
SOURCES = [
    ("src.rag.character.character_types", "character.ts"),
    ("api.database.firestore_models", "firestore.ts"),
    ("api.schemas.character", "schemas_character.ts"),
    ("api.schemas.feedback", "schemas_feedback.ts"),
]


def find_pydantic2ts():
    """Find the pydantic2ts executable."""
    pydantic2ts = shutil.which("pydantic2ts")
    if pydantic2ts:
        return pydantic2ts
    return None


def find_json2ts():
    """
    Locate the `json2ts` executable by checking the project's frontend local node_modules first, then the system PATH.
    
    Returns:
        str | None: Path to the `json2ts` executable as a string if found, otherwise `None`.
    """
    # Check if it's in frontend node_modules
    local_json2ts = FRONTEND_DIR / "node_modules" / ".bin" / "json2ts"
    if local_json2ts.exists():
        return str(local_json2ts)

    # Check if it's globally installed
    global_json2ts = shutil.which("json2ts")
    if global_json2ts:
        return global_json2ts

    return None


def main():
    """
    Generate TypeScript type definitions from the configured Pydantic modules and create a barrel export.
    
    Runs pydantic2ts for each module listed in SOURCES, writes generated .ts files into GENERATED_DIR, and if at least one file is produced writes an index.ts that re-exports the generated modules (excluding firestore.ts). Prints progress and error output for each module. Exits the process with status 1 if json2ts cannot be found or if not all sources were successfully generated.
    """
    # Find pydantic2ts
    pydantic2ts_cmd = find_pydantic2ts()
    if not pydantic2ts_cmd:
        print("Error: pydantic2ts not found. Install it with:")
        print("  uv add pydantic-to-typescript")
        sys.exit(1)

    # Find json2ts
    json2ts_cmd = find_json2ts()
    if not json2ts_cmd:
        print("Error: json2ts not found. Install it with:")
        print("  cd frontend && npm install json-schema-to-typescript")
        sys.exit(1)

    # Ensure output directory exists
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating TypeScript types to: {GENERATED_DIR}")
    print(f"Using pydantic2ts: {pydantic2ts_cmd}")
    print(f"Using json2ts: {json2ts_cmd}")

    success_count = 0
    for module, output_file in SOURCES:
        output_path = GENERATED_DIR / output_file
        print(f"  {module} -> {output_file}...")

        try:
            result = subprocess.run(
                [
                    pydantic2ts_cmd,
                    "--module", module,
                    "--output", str(output_path),
                    "--json2ts-cmd", json2ts_cmd,
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"    Error: {e.stderr}")
            continue

    # Generate barrel export
    # Note: firestore.ts has naming conflicts with schemas_feedback.ts (FeedbackStats)
    # so we exclude it from the barrel export - import firestore types directly when needed
    if success_count > 0:
        exports = []
        for _, output_file in SOURCES:
            # Skip firestore to avoid naming conflicts
            if output_file == "firestore.ts":
                continue
            ts_file = GENERATED_DIR / output_file
            if ts_file.exists():
                module_name = output_file.replace(".ts", "")
                exports.append(f"export * from './{module_name}';")

        # Add comment about firestore
        exports.append("// Note: firestore.ts excluded due to naming conflicts with schemas_feedback.ts")
        exports.append("// Import firestore types directly: import type { ... } from '@/lib/types/generated/firestore'")

        index_path = GENERATED_DIR / "index.ts"
        index_path.write_text("\n".join(exports) + "\n")
        print(f"\nGenerated barrel export: {index_path}")

    print(f"\nSuccessfully generated {success_count}/{len(SOURCES)} type files")

    if success_count < len(SOURCES):
        sys.exit(1)


if __name__ == "__main__":
    main()