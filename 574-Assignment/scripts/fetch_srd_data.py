"""
Fetch D&D 5e SRD data from the official API.

This script fetches all entity data from https://www.dnd5eapi.co/api/2014/
and caches it locally for use in dataset generation.

Usage:
    uv run python -m scripts.fetch_srd_data
    
The SRD data is static (rarely changes), so this only needs to run once.
"""

import json
import requests
from pathlib import Path
from typing import Any

# API configuration
BASE_URL = "https://www.dnd5eapi.co/api/2014"

# Cache directory
CACHE_DIR = Path(__file__).parent.parent / "data" / "srd_cache"

# Endpoints to fetch
ENDPOINTS = [
    "spells",
    "monsters", 
    "equipment",
    "magic-items",
    "features",
    "conditions",
    "classes",
    "races",
    "subclasses",
    "traits",
    "skills",
    "ability-scores",
    "damage-types",
    "weapon-properties",
    "proficiencies",
    "languages",
    "alignments",
    "backgrounds",
]


def fetch_endpoint(endpoint: str) -> dict[str, Any]:
    """Fetch all items from an API endpoint."""
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_item_details(url: str) -> dict[str, Any]:
    """Fetch detailed info for a specific item."""
    full_url = f"https://www.dnd5eapi.co{url}"
    response = requests.get(full_url, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_and_cache_all():
    """Fetch all endpoints and cache locally."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    summary = {}
    
    for endpoint in ENDPOINTS:
        cache_file = CACHE_DIR / f"{endpoint}.json"
        
        print(f"Fetching {endpoint}...")
        try:
            data = fetch_endpoint(endpoint)
            
            # Save to cache
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)
            
            count = data.get("count", len(data.get("results", [])))
            summary[endpoint] = count
            print(f"  ✓ {count} items cached to {cache_file.name}")
            
        except requests.RequestException as e:
            print(f"  ✗ Failed to fetch {endpoint}: {e}")
            summary[endpoint] = 0
    
    # Save summary
    summary_file = CACHE_DIR / "summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'='*50}")
    print("Fetch complete! Summary:")
    print(f"{'='*50}")
    total = 0
    for endpoint, count in summary.items():
        print(f"  {endpoint}: {count}")
        total += count
    print(f"{'='*50}")
    print(f"  TOTAL: {total} entities")
    
    return summary


def load_cached_data(endpoint: str) -> dict[str, Any] | None:
    """Load cached data for an endpoint."""
    cache_file = CACHE_DIR / f"{endpoint}.json"
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)
    return None


def get_entity_names(endpoint: str) -> list[str]:
    """Get list of entity names from cached data."""
    data = load_cached_data(endpoint)
    if data and "results" in data:
        return [item["name"] for item in data["results"]]
    return []


def get_entity_map(endpoint: str) -> dict[str, str]:
    """Get mapping of entity names to their API index (slug)."""
    data = load_cached_data(endpoint)
    if data and "results" in data:
        return {item["name"]: item["index"] for item in data["results"]}
    return {}


if __name__ == "__main__":
    fetch_and_cache_all()
