#!/usr/bin/env python3
"""
Build the D&D 5e Rulebook Storage System

This script parses the D&D 5e rulebook markdown file, categorizes sections,
generates embeddings using OpenAI, and saves the complete storage system.
"""

import sys
from pathlib import Path
import time
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag.rulebook.rulebook_storage import RulebookStorage


def main():
    """Main build process"""
    parser = argparse.ArgumentParser(description="Build D&D 5e Rulebook Storage")
    parser.add_argument("--force", action="store_true", help="Force rebuild from scratch")
    args = parser.parse_args()
    
    print("🐲 Building D&D 5e Rulebook Storage System")
    print("=" * 50)
    
    # Initialize storage
    storage = RulebookStorage()
    
    # Check if we should load existing data
    if storage.load_from_disk():
        print("\n📂 Existing storage found")
        stats = storage.get_stats()
        print(f"Loaded: {stats['total_sections']} sections")
        print(f"Embeddings: {stats['embedding_coverage']}")
        
        if not args.force:
            # Ask if user wants to rebuild
            response = input("\nDo you want to rebuild from scratch? (y/N): ").lower()
            if response not in ['y', 'yes']:
                print("Using existing storage. Run with --force to rebuild.")
                return
        else:
            print("\n🔄 Force rebuild requested...")
        
        # Clear existing data for rebuild
        storage.sections.clear()
        storage.category_index = {cat: set() for cat in storage.category_index.keys()}
    
    # Parse the rulebook
    print("\n📖 Parsing D&D 5e Rulebook...")
    rulebook_path = project_root / "knowledge_base" / "source" / "dnd5rulebook.md"
    
    if not rulebook_path.exists():
        print(f"❌ Error: Rulebook file not found at {rulebook_path}")
        print("Please ensure the dnd5rulebook.md file exists in the knowledge_base/source directory.")
        return
    
    start_time = time.time()
    storage.parse_markdown(str(rulebook_path))
    parse_time = time.time() - start_time
    
    print(f"\n✅ Parsing complete in {parse_time:.2f} seconds")
    
    # Show parsing stats
    stats = storage.get_stats()
    print(f"📊 Parsed {stats['total_sections']} sections:")
    for level, count in sorted(stats['level_counts'].items()):
        print(f"  {level}: {count}")
    
    print(f"\n📂 Category distribution:")
    for category, count in stats['category_counts'].items():
        if count > 0:
            print(f"  {category}: {count}")
    
    # Generate embeddings
    print(f"\n🧠 Generating embeddings using {storage.embedding_model}...")
    embed_start = time.time()
    storage.generate_embeddings(batch_size=20)  # Smaller batches for stability
    embed_time = time.time() - embed_start
    
    print(f"✅ Embedding generation complete in {embed_time:.2f} seconds")
    
    # Save to disk
    print(f"\n💾 Saving storage system...")
    storage.save_to_disk()
    
    # Final stats
    final_stats = storage.get_stats()
    total_time = time.time() - start_time
    
    print(f"\n🎉 Build Complete!")
    print("=" * 50)
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Sections: {final_stats['total_sections']}")
    print(f"Embeddings: {final_stats['embedding_coverage']}")
    print(f"Storage saved to: knowledge_base/processed_rulebook/")
    
    # Show sample sections
    print(f"\n📋 Sample sections:")
    sample_count = 0
    for section_id, section in storage.sections.items():
        if sample_count >= 5:
            break
        print(f"  {section.title} (Level {section.level}, {len(section.categories)} categories)")
        sample_count += 1
    
    print(f"\n✨ Ready for semantic search and content retrieval!")


if __name__ == "__main__":
    main()
