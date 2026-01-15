#!/usr/bin/env python3
"""
Migrate Rulebook Storage from Pickle to JSON
"""

import sys
from pathlib import Path
import os
import pickle
import json
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag.rulebook.rulebook_storage import RulebookStorage

def convert_numpy(obj):
    if hasattr(obj, 'tolist'):
        return obj.tolist()
    return obj

def main():
    print("Migrating Rulebook Storage from Pickle to JSON...")

    storage = RulebookStorage()
    pkl_file = "rulebook_storage.pkl"
    pkl_path = storage.storage_path / pkl_file

    if not pkl_path.exists():
        print(f"Error: {pkl_file} not found at {pkl_path}")
        return

    print(f"Loading from {pkl_file} using pickle...")
    try:
        with open(pkl_path, 'rb') as f:
            save_data = pickle.load(f)
    except Exception as e:
        print(f"Failed to load pickle file: {e}")
        return

    # Process sections to convert numpy arrays
    sections_dict = save_data.get('sections', {})
    for sid, s_dict in sections_dict.items():
        if s_dict.get('vector') is not None:
            s_dict['vector'] = convert_numpy(s_dict['vector'])

    # Save to JSON
    json_file = "rulebook_storage.json"
    json_path = storage.storage_path / json_file
    print(f"Saving to {json_file}...")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, indent=2)

    print(f"Saved {len(sections_dict)} sections to disk")

    # Verify load using RulebookStorage
    print("Verifying JSON load...")
    verify_storage = RulebookStorage()
    # verify_storage.load_from_disk defaults to json now
    verify_success = verify_storage.load_from_disk(json_file)

    if verify_success:
        print(f"Successfully migrated {len(verify_storage.sections)} sections to JSON.")
        print(f"File saved at: {json_path}")
    else:
        print("Verification failed!")

if __name__ == "__main__":
    main()
