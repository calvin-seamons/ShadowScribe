#!/usr/bin/env python3
"""
Rebuild embeddings for the rulebook storage when changing embedding models.
This script will regenerate all embeddings using the current config model.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag.rulebook.rulebook_storage import RulebookStorage
from src.config import get_config
import time


def rebuild_embeddings():
    """Rebuild all embeddings using the current config model"""
    config = get_config()
    
    print("Rebuilding Rulebook Embeddings")
    print("=" * 40)
    print(f"Target embedding model: {config.embedding_model}")
    print(f"Expected dimensions: {config.get_embedding_dimensions()}")
    print()
    
    # Load existing storage
    storage = RulebookStorage()
    
    # Check if storage file exists
    storage_file = storage.storage_path / "rulebook_storage.json"
    if not storage_file.exists():
        print("❌ No existing storage file found.")
        print("   Please run: python -m scripts.build_rulebook_storage")
        return
    
    # Load sections (this will show the mismatch warning if applicable)
    success = storage.load_from_disk()
    if not success:
        print("❌ Failed to load existing storage")
        return
    
    print()
    print("Clearing existing embeddings...")
    
    # Clear all existing embeddings
    cleared_count = 0
    for section in storage.sections.values():
        if section.vector is not None:
            section.vector = None
            cleared_count += 1
    
    print(f"✓ Cleared {cleared_count} embeddings")
    print()
    
    # Update the storage model to current config
    old_model = storage.embedding_model
    storage.embedding_model = config.embedding_model
    
    print(f"Model change: {old_model} → {config.embedding_model}")
    print()
    
    # Regenerate embeddings
    print("Generating new embeddings...")
    start_time = time.time()
    
    try:
        storage.generate_embeddings()
        
        # Save updated storage
        storage.save_to_disk()
        
        elapsed = time.time() - start_time
        print()
        print("✓ Embedding rebuild completed!")
        print(f"  Time taken: {elapsed:.2f} seconds")
        print(f"  Model: {config.embedding_model}")
        print(f"  Sections: {len(storage.sections)}")
        
        # Show stats
        sections_with_embeddings = sum(1 for s in storage.sections.values() if s.vector is not None)
        print(f"  Embedded: {sections_with_embeddings}/{len(storage.sections)}")
        
    except Exception as e:
        print(f"❌ Error during embedding generation: {e}")
        print("   Check your API key and network connection")


def main():
    """Main entry point"""
    try:
        rebuild_embeddings()
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
