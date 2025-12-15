#!/usr/bin/env python3
"""
Build Contextual Embeddings for D&D 5e Rulebook

This script generates Claude-powered contextual prefixes for each rulebook section,
following Anthropic's Contextual Retrieval approach to improve retrieval accuracy.

Each chunk gets a 50-100 token context prefix that situates it within the broader
document structure, making embeddings more semantically meaningful.

Usage:
    uv run python -m scripts.build_contextual_embeddings
    uv run python -m scripts.build_contextual_embeddings --dry-run
    uv run python -m scripts.build_contextual_embeddings --batch-size 10
"""

import sys
from pathlib import Path
import time
import argparse
import json
import pickle
from typing import Optional, Dict, List
from dataclasses import dataclass
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

from src.rag.rulebook.rulebook_storage import RulebookStorage
from src.rag.rulebook.rulebook_types import RulebookSection, RulebookCategory


# Anthropic model for context generation (Haiku is fast and cheap)
CONTEXT_MODEL = "claude-haiku-4-5"

# Prompt template following Anthropic's contextual retrieval approach
CONTEXT_PROMPT = """<document>
{document_context}
</document>

Here is the chunk we want to situate within the whole document:
<chunk>
{chunk_content}
</chunk>

Please give a short succinct context to situate this chunk within the overall D&D 5e rulebook for the purposes of improving search retrieval of the chunk. Include:
- What chapter/section this belongs to
- What broader topic this relates to (e.g., "combat mechanics", "spellcasting rules", "character creation")
- Any key terms or concepts that should be associated with this chunk

Answer only with the succinct context (50-100 tokens) and nothing else."""


@dataclass
class ContextGenerationStats:
    """Track statistics for context generation"""
    total_sections: int = 0
    sections_processed: int = 0
    sections_skipped: int = 0
    sections_failed: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    elapsed_time_seconds: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "total_sections": self.total_sections,
            "sections_processed": self.sections_processed,
            "sections_skipped": self.sections_skipped,
            "sections_failed": self.sections_failed,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": self.total_cost_usd,
            "elapsed_time_seconds": self.elapsed_time_seconds,
        }


class ContextualEmbeddingBuilder:
    """Builds contextual prefixes for rulebook sections using Claude"""
    
    # Pricing for Claude 3.5 Haiku (per 1M tokens) - December 2024
    INPUT_PRICE_PER_1M = 1.00  # $1.00 per 1M input tokens
    OUTPUT_PRICE_PER_1M = 5.00  # $5.00 per 1M output tokens
    
    def __init__(self, storage: RulebookStorage, dry_run: bool = False):
        self.storage = storage
        self.dry_run = dry_run
        self.stats = ContextGenerationStats()
        
        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        self.client = Anthropic(api_key=api_key)
        
        # Storage path for contextual data
        self.context_storage_path = Path("knowledge_base/processed_rulebook/contextual_prefixes.json")
        
        # Load existing contextual prefixes if available
        self.contextual_prefixes: Dict[str, str] = {}
        self._load_existing_prefixes()
    
    def _load_existing_prefixes(self) -> None:
        """Load any existing contextual prefixes"""
        if self.context_storage_path.exists():
            with open(self.context_storage_path, 'r', encoding='utf-8') as f:
                self.contextual_prefixes = json.load(f)
            print(f"📂 Loaded {len(self.contextual_prefixes)} existing contextual prefixes")
    
    def _save_prefixes(self) -> None:
        """Save contextual prefixes to disk"""
        self.context_storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.context_storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.contextual_prefixes, f, indent=2)
        print(f"💾 Saved {len(self.contextual_prefixes)} contextual prefixes")
    
    def _get_document_context(self, section: RulebookSection) -> str:
        """Build document context for a section (parent hierarchy + siblings)"""
        context_parts = []
        
        # Get parent chain (chapter -> section hierarchy)
        parent_chain = []
        current_id = section.parent_id
        while current_id and current_id in self.storage.sections:
            parent = self.storage.sections[current_id]
            parent_chain.append(parent)
            current_id = parent.parent_id
        
        # Add parent context (reverse to go from chapter down)
        for parent in reversed(parent_chain):
            level_name = "Chapter" if parent.level == 1 else f"Section (Level {parent.level})"
            context_parts.append(f"{level_name}: {parent.title}")
            # Add brief parent content summary (first 200 chars)
            if parent.content.strip():
                summary = parent.content[:200].strip()
                if len(parent.content) > 200:
                    summary += "..."
                context_parts.append(f"Summary: {summary}")
        
        # Add sibling context (other sections at same level under same parent)
        if section.parent_id and section.parent_id in self.storage.sections:
            parent = self.storage.sections[section.parent_id]
            siblings = [
                self.storage.sections[sid].title 
                for sid in parent.children_ids 
                if sid != section.id and sid in self.storage.sections
            ][:5]  # Limit to 5 siblings
            if siblings:
                context_parts.append(f"Related sections: {', '.join(siblings)}")
        
        # Add category context
        if section.categories:
            cat_names = [cat.name.replace('_', ' ').title() for cat in section.categories]
            context_parts.append(f"Categories: {', '.join(cat_names)}")
        
        return "\n".join(context_parts) if context_parts else "This is a top-level section of the D&D 5e rulebook."
    
    def _generate_context_for_section(self, section: RulebookSection) -> Optional[str]:
        """Generate contextual prefix for a single section using Claude"""
        # Skip if already has context
        if section.id in self.contextual_prefixes:
            return self.contextual_prefixes[section.id]
        
        # Skip sections with no content
        if not section.content.strip():
            return None
        
        # Build the document context
        document_context = self._get_document_context(section)
        
        # Build chunk content (title + content, limited)
        chunk_content = f"Title: {section.title}\n\n{section.content}"
        if len(chunk_content) > 2000:
            chunk_content = chunk_content[:2000] + "..."
        
        # Build the prompt
        prompt = CONTEXT_PROMPT.format(
            document_context=document_context,
            chunk_content=chunk_content
        )
        
        if self.dry_run:
            # In dry run, estimate tokens and return placeholder
            estimated_input = len(prompt) // 4  # Rough estimate
            estimated_output = 75  # Target output
            self.stats.total_input_tokens += estimated_input
            self.stats.total_output_tokens += estimated_output
            return f"[DRY RUN] Context for: {section.title}"
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model=CONTEXT_MODEL,
                max_tokens=150,  # Keep context concise
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract response
            context = response.content[0].text.strip()
            
            # Track token usage
            self.stats.total_input_tokens += response.usage.input_tokens
            self.stats.total_output_tokens += response.usage.output_tokens
            
            return context
            
        except Exception as e:
            print(f"  ❌ Error generating context for {section.id}: {e}")
            self.stats.sections_failed += 1
            return None
    
    def _calculate_cost(self) -> float:
        """Calculate estimated cost based on token usage"""
        input_cost = (self.stats.total_input_tokens / 1_000_000) * self.INPUT_PRICE_PER_1M
        output_cost = (self.stats.total_output_tokens / 1_000_000) * self.OUTPUT_PRICE_PER_1M
        return input_cost + output_cost
    
    def build_all_contexts(self, batch_size: int = 20, save_interval: int = 50) -> ContextGenerationStats:
        """Generate contextual prefixes for all sections"""
        start_time = time.time()
        
        # Get all sections that need context
        sections_to_process = [
            s for s in self.storage.sections.values()
            if s.id not in self.contextual_prefixes and s.content.strip()
        ]
        
        self.stats.total_sections = len(self.storage.sections)
        sections_already_done = len(self.contextual_prefixes)
        
        print(f"\n🧠 Building Contextual Embeddings")
        print("=" * 50)
        print(f"Total sections: {self.stats.total_sections}")
        print(f"Already processed: {sections_already_done}")
        print(f"To process: {len(sections_to_process)}")
        print(f"Model: {CONTEXT_MODEL}")
        print(f"Dry run: {self.dry_run}")
        print()
        
        if not sections_to_process:
            print("✅ All sections already have contextual prefixes!")
            return self.stats
        
        # Process sections
        for i, section in enumerate(sections_to_process):
            # Progress indicator
            if (i + 1) % 10 == 0 or i == 0:
                cost = self._calculate_cost()
                print(f"Processing {i + 1}/{len(sections_to_process)} - Cost: ${cost:.4f}")
            
            # Generate context
            context = self._generate_context_for_section(section)
            
            if context:
                self.contextual_prefixes[section.id] = context
                self.stats.sections_processed += 1
                print(f"  ✓ {section.title[:50]}...")
            else:
                self.stats.sections_skipped += 1
            
            # Save periodically
            if (i + 1) % save_interval == 0 and not self.dry_run:
                self._save_prefixes()
                print(f"  💾 Checkpoint saved ({len(self.contextual_prefixes)} prefixes)")
            
            # Small delay to avoid rate limits
            if not self.dry_run:
                time.sleep(0.05)
        
        # Final save
        if not self.dry_run:
            self._save_prefixes()
        
        # Calculate final stats
        self.stats.elapsed_time_seconds = time.time() - start_time
        self.stats.total_cost_usd = self._calculate_cost()
        
        return self.stats
    
    def get_contextualized_text(self, section: RulebookSection) -> str:
        """Get the contextualized text for embedding (prefix + content)"""
        prefix = self.contextual_prefixes.get(section.id, "")
        if prefix:
            return f"{prefix}\n\n{section.title}\n\n{section.content}"
        else:
            return f"{section.title}\n\n{section.content}"


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Build Contextual Embeddings for D&D 5e Rulebook")
    parser.add_argument("--dry-run", action="store_true", help="Estimate costs without making API calls")
    parser.add_argument("--batch-size", type=int, default=20, help="Batch size for processing")
    parser.add_argument("--save-interval", type=int, default=50, help="Save checkpoint every N sections")
    args = parser.parse_args()
    
    print("🐲 D&D 5e Rulebook Contextual Embedding Builder")
    print("=" * 50)
    
    # Load existing rulebook storage
    storage = RulebookStorage()
    if not storage.load_from_disk():
        print("❌ Error: Rulebook storage not found!")
        print("Please run 'uv run python -m scripts.build_rulebook_storage' first.")
        return 1
    
    print(f"📖 Loaded {len(storage.sections)} sections from rulebook storage")
    
    # Initialize builder
    try:
        builder = ContextualEmbeddingBuilder(storage, dry_run=args.dry_run)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return 1
    
    # Build contexts
    stats = builder.build_all_contexts(
        batch_size=args.batch_size,
        save_interval=args.save_interval
    )
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Summary")
    print("=" * 50)
    print(f"Total sections:     {stats.total_sections}")
    print(f"Processed:          {stats.sections_processed}")
    print(f"Skipped (empty):    {stats.sections_skipped}")
    print(f"Failed:             {stats.sections_failed}")
    print(f"Input tokens:       {stats.total_input_tokens:,}")
    print(f"Output tokens:      {stats.total_output_tokens:,}")
    print(f"Estimated cost:     ${stats.total_cost_usd:.4f}")
    print(f"Elapsed time:       {stats.elapsed_time_seconds:.2f}s")
    
    if args.dry_run:
        print("\n⚠️  This was a dry run. No API calls were made.")
        print("Run without --dry-run to generate actual contexts.")
    else:
        print(f"\n✅ Contextual prefixes saved to: {builder.context_storage_path}")
        print("\n📝 Next steps:")
        print("1. The contextual prefixes are stored separately from embeddings")
        print("2. Modify rulebook_storage.py to use contextualized text for embeddings")
        print("3. Regenerate embeddings with: uv run python -m scripts.rebuild_embeddings")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
