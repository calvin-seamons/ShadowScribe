"""
D&D 5e Rulebook Storage System - Main Storage Class and Parser
"""

from typing import List, Dict, Optional, Set, Tuple
import re
import os
import json
import pickle
from pathlib import Path
import hashlib
from dataclasses import dataclass, field
import time

from .rulebook_types import RulebookSection, RulebookCategory, SearchResult, RULEBOOK_CATEGORY_ASSIGNMENTS, MULTI_CATEGORY_SECTIONS
from .categorizer import RulebookCategorizer
from ...config import get_config
from ...embeddings import get_embedding_provider, EmbeddingProvider

# Note: dotenv is loaded in config.py


class RulebookStorage:
    """Storage and retrieval system for D&D 5e rulebook sections"""
    
    def __init__(self, storage_path: str = "knowledge_base/processed_rulebook"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Get configuration
        self.config = get_config()
        
        # Core data structures
        self.sections: Dict[str, RulebookSection] = {}
        self.category_index: Dict[RulebookCategory, Set[str]] = {cat: set() for cat in RulebookCategory}
        self.embedding_model = self.config.embedding_model
        
        # Initialize categorizer with the same logic as check_category_coverage.py
        self.categorizer = RulebookCategorizer()
        
        # Initialize embedding provider (supports both OpenAI and local models)
        self._embedding_provider: Optional[EmbeddingProvider] = None
    
    def parse_markdown(self, markdown_path: str) -> None:
        """Parse the D&D 5e rulebook markdown into sections using two-phase approach"""
        print(f"Parsing markdown file: {markdown_path}")
        
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Phase 1: Extract all headers and their structure
        headers = self._extract_headers(content)
        print(f"Found {len(headers)} headers")
        
        # Phase 2: Categorize all sections using full context
        print("Categorizing sections...")
        categorizations = self.categorizer.categorize_all_sections(headers)
        
        # Phase 3: Create sections with content and apply categorizations
        print("Creating sections with content...")
        self._create_sections_with_content(content, headers, categorizations)
        
        print(f"Parsed {len(self.sections)} sections total")
    
    def _extract_headers(self, content: str) -> List[Tuple[str, int, str]]:
        """Extract all headers from markdown content"""
        headers = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            header_match = re.match(r'^(#{1,6})\s+(.+?)(?:\s+\{#([^}]+)\})?$', line)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                section_id = header_match.group(3) if header_match.group(3) else self._generate_section_id(title)
                headers.append((section_id, level, title))
        
        return headers
    
    def _create_sections_with_content(self, content: str, headers: List[Tuple[str, int, str]], categorizations: Dict[str, List[RulebookCategory]]) -> None:
        """Create sections for ALL headers with content and apply categorizations"""
        lines = content.split('\n')
        
        # Create a map of header positions in the content
        header_positions = {}
        for i, line in enumerate(lines):
            line = line.strip()
            header_match = re.match(r'^(#{1,6})\s+(.+?)(?:\s+\{#([^}]+)\})?$', line)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                section_id = header_match.group(3) if header_match.group(3) else self._generate_section_id(title)
                header_positions[section_id] = i
        
        # Track hierarchy
        current_sections: Dict[int, RulebookSection] = {}
        
        # Process ALL headers from the headers list
        for section_id, level, title in headers:
            # Get content for this header if it exists in the markdown
            section_content = ""
            if section_id in header_positions:
                # Collect content until next header
                content_lines = []
                start_line = header_positions[section_id] + 1
                
                j = start_line
                while j < len(lines):
                    next_line = lines[j].strip()
                    if re.match(r'^#{1,6}\s+', next_line):
                        break
                    content_lines.append(lines[j])
                    j += 1
                
                section_content = '\n'.join(content_lines).strip()
            
            # Get categories from our categorization
            categories = categorizations.get(section_id, [])
            
            # Create section (even if content is empty)
            section = RulebookSection(
                id=section_id,
                title=title,
                level=level,
                content=section_content,
                parent_id=None,
                children_ids=[],
                categories=categories,
                metadata={}
            )
            
            # Handle hierarchy
            if level == 1:
                current_sections = {1: section}
            else:
                # Find parent - closest section at lower level
                parent = None
                for parent_level in range(level - 1, 0, -1):
                    if parent_level in current_sections:
                        parent = current_sections[parent_level]
                        break
                
                if parent:
                    section.parent_id = parent.id
                    parent.children_ids.append(section.id)
                
                # Update current sections at this level and clear deeper levels
                current_sections[level] = section
                for clear_level in list(current_sections.keys()):
                    if clear_level > level:
                        del current_sections[clear_level]
            
            # Add to storage
            self.sections[section_id] = section
            
            # Update category index
            for category in section.categories:
                self.category_index[category].add(section_id)
    
    def _generate_section_id(self, title: str) -> str:
        """Generate a section ID from title"""
        # Convert to lowercase and replace spaces/special chars with hyphens
        section_id = re.sub(r'[^a-z0-9\s-]', '', title.lower())
        section_id = re.sub(r'\s+', '-', section_id)
        section_id = re.sub(r'-+', '-', section_id)  # Collapse multiple hyphens
        section_id = section_id.strip('-')  # Remove leading/trailing hyphens
        return section_id
    
    def _get_embedding_provider(self) -> EmbeddingProvider:
        """Get or initialize the embedding provider (lazy loading)"""
        if self._embedding_provider is None:
            self._embedding_provider = get_embedding_provider(self.embedding_model)
            print(f"Using embedding model: {self._embedding_provider.model_name} ({self._embedding_provider.embedding_dim} dimensions)")
        return self._embedding_provider
    
    def generate_embeddings(self, batch_size: int = 50) -> None:
        """Generate embeddings for all sections that don't have them"""
        sections_to_embed = [s for s in self.sections.values() if s.vector is None]
        
        if not sections_to_embed:
            print("All sections already have embeddings")
            return
        
        print(f"Generating embeddings for {len(sections_to_embed)} sections...")
        
        # Get embedding provider
        provider = self._get_embedding_provider()
        is_local = self.config.is_local_model()
        
        # Process in batches
        for i in range(0, len(sections_to_embed), batch_size):
            batch = sections_to_embed[i:i + batch_size]
            print(f"Processing batch {i // batch_size + 1}/{(len(sections_to_embed) + batch_size - 1) // batch_size}")
            
            # Prepare texts for embedding
            texts = []
            for section in batch:
                # Create combined text for embedding: title + content
                # Handle empty content gracefully - use just title if content is empty
                if section.content.strip():
                    embedding_text = f"{section.title}\n\n{section.content}"
                else:
                    embedding_text = section.title
                
                # Limit text length (embeddings have token limits)
                if len(embedding_text) > 8000:  # Conservative limit
                    embedding_text = embedding_text[:8000] + "..."
                texts.append(embedding_text)
            
            try:
                # Generate embeddings using the provider
                embeddings = provider.embed_batch(texts, show_progress=False)
                
                # Store embeddings
                for j, section in enumerate(batch):
                    section.vector = embeddings[j]
                    print(f"  Generated embedding for: {section.title}")
                
                # Small delay for API-based models to avoid rate limits
                if not is_local:
                    time.sleep(0.1)
                
            except Exception as e:
                print(f"Error generating embeddings for batch: {e}")
                # Continue with next batch
                continue
        
        print("Embedding generation complete")
    
    def save_to_disk(self, filename: str = "rulebook_storage.pkl") -> None:
        """Save the entire storage system to disk"""
        filepath = self.storage_path / filename
        
        # Prepare data for serialization
        save_data = {
            'sections': {sid: section.to_dict() for sid, section in self.sections.items()},
            'category_index': {cat.value: list(section_ids) for cat, section_ids in self.category_index.items()},
            'embedding_model': self.embedding_model
        }
        
        print(f"Saving rulebook storage to: {filepath}")
        with open(filepath, 'wb') as f:
            pickle.dump(save_data, f)
        
        print(f"Saved {len(self.sections)} sections to disk")
    
    def load_from_disk(self, filename: str = "rulebook_storage.pkl") -> bool:
        """Load the storage system from disk"""
        filepath = self.storage_path / filename
        
        if not filepath.exists():
            print(f"Storage file not found: {filepath}")
            return False
        
        print(f"Loading rulebook storage from: {filepath}")
        with open(filepath, 'rb') as f:
            save_data = pickle.load(f)
        
        # Restore sections
        self.sections = {}
        for sid, section_data in save_data['sections'].items():
            self.sections[sid] = RulebookSection.from_dict(section_data)
        
        # Restore category index
        self.category_index = {}
        for cat_value, section_ids in save_data['category_index'].items():
            category = RulebookCategory(cat_value)
            self.category_index[category] = set(section_ids)
        
        self.embedding_model = save_data.get('embedding_model', 'text-embedding-3-large')
        
        # Check for embedding model mismatch
        if self.embedding_model != self.config.embedding_model:
            print(f"⚠️  Embedding model mismatch!")
            print(f"   Stored model: {self.embedding_model}")
            print(f"   Config model: {self.config.embedding_model}")
            print(f"   You may want to regenerate embeddings for optimal performance.")
            print(f"   Use: python -m scripts.rebuild_embeddings")
        
        print(f"Loaded {len(self.sections)} sections from disk")
        return True
    
    def get_stats(self) -> Dict:
        """Get statistics about the storage system"""
        total_sections = len(self.sections)
        sections_with_embeddings = sum(1 for s in self.sections.values() if s.vector is not None)
        
        category_counts = {}
        for category, section_ids in self.category_index.items():
            category_counts[category.name] = len(section_ids)
        
        level_counts = {}
        for section in self.sections.values():
            level_counts[f"Level {section.level}"] = level_counts.get(f"Level {section.level}", 0) + 1
        
        return {
            'total_sections': total_sections,
            'sections_with_embeddings': sections_with_embeddings,
            'embedding_coverage': f"{sections_with_embeddings}/{total_sections} ({100 * sections_with_embeddings / total_sections:.1f}%)" if total_sections > 0 else "0%",
            'category_counts': category_counts,
            'level_counts': level_counts,
            'embedding_model': self.embedding_model
        }
