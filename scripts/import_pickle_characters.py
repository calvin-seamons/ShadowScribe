#!/usr/bin/env python3
"""Import pickle characters into the database via the API."""

import pickle
import json
import requests
from pathlib import Path
from dataclasses import asdict
from datetime import datetime


def serialize_for_json(obj):
    """Recursively convert datetime objects to ISO format strings."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    return obj


def import_character(pkl_path: Path, api_url: str = "http://localhost:8000") -> bool:
    """Import a single character from pickle file to database."""
    print(f"Loading: {pkl_path.name}")
    
    with open(pkl_path, 'rb') as f:
        character = pickle.load(f)
    
    # Convert to dict and handle datetime serialization
    char_dict = serialize_for_json(asdict(character))
    
    # Send to API
    response = requests.post(
        f"{api_url}/api/characters",
        json={"character": char_dict},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ Imported: {data.get('name')} (Level {data.get('level')} {data.get('race')} {data.get('character_class')})")
        return True
    else:
        print(f"  ❌ Error: {response.text[:200]}")
        return False


def main():
    """Import all pickle characters from saved_characters directory."""
    saved_dir = Path("knowledge_base/saved_characters")
    
    if not saved_dir.exists():
        print(f"Directory not found: {saved_dir}")
        return
    
    pkl_files = list(saved_dir.glob("*.pkl"))
    
    if not pkl_files:
        print("No pickle files found")
        return
    
    print(f"Found {len(pkl_files)} character(s) to import\n")
    
    success = 0
    for pkl_path in pkl_files:
        if import_character(pkl_path):
            success += 1
    
    print(f"\nImported {success}/{len(pkl_files)} characters")


if __name__ == "__main__":
    main()
