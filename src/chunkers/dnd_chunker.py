"""
D&D 5e Rulebook Chunker

Specialized chunker for D&D 5e System Reference Document content.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from tqdm import tqdm
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document as LangChainDocument
from langchain_community.vectorstores.utils import filter_complex_metadata

from config.settings import Config
from utils.helpers import TokenCounter, ProgressTracker
from chunkers.markdown_parser import MarkdownHierarchyParser


class DNDRulebookChunker:
    """Chunker specifically designed for D&D 5e rulebook content"""
    
    def __init__(self, config: Config):
        self.config = config
        self.parser = MarkdownHierarchyParser()
        self.token_counter = TokenCounter()
        self.logger = logging.getLogger(__name__)
        self.progress_tracker = ProgressTracker()
    
    def determine_content_type(self, header_path: List[str], content: str) -> str:
        """Enhanced content type detection"""
        if not header_path:
            return 'general'
        
        path_lower = [h.lower() for h in header_path]
        
        # More specific type detection
        if 'legal information' in ' '.join(path_lower):
            return 'legal'
        
        if len(path_lower) >= 1:
            if 'races' in path_lower[0] or 'race' in path_lower[0]:
                if len(path_lower) == 2:
                    return 'race'
                elif any(trait in path_lower[-1] for trait in ['traits', 'trait']):
                    return 'racial_trait'
                else:
                    return 'trait'
            
            elif 'classes' in path_lower[0] or 'class' in path_lower[0]:
                if len(path_lower) == 2:
                    return 'class'
                elif any(keyword in path_lower[-1] for keyword in ['path', 'college', 'domain', 'circle']):
                    return 'subclass'
                elif 'features' in path_lower[-1] or 'feature' in path_lower[-1]:
                    return 'class_feature'
                else:
                    return 'feature'
            
            elif 'spells' in path_lower[0] or 'spell' in path_lower[0]:
                return 'spell'
            
            elif 'equipment' in path_lower[0] or 'items' in path_lower[0]:
                return 'equipment'
        
        # Check for tables
        if '<table' in content.lower() or content.count('|') > 5:
            return 'table'
        
        return 'general'
    
    def extract_level_info(self, content: str) -> Optional[str]:
        """Extract level information from content"""
        level_patterns = [
            r'(\d+(?:st|nd|rd|th)\s+level)',
            r'level\s+(\d+)',
            r'at\s+(\d+(?:st|nd|rd|th))\s+level'
        ]
        
        for pattern in level_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def create_metadata(self, header_info: Dict[str, Any], content: str, source: str) -> Dict[str, Any]:
        """Create metadata for a chunk"""
        content_type = self.determine_content_type(header_info['full_path'], content)
        level_info = self.extract_level_info(content)
        
        metadata = {
            'source': source,
            'type': content_type,
            'name': header_info['text'],
            'headers': ' > '.join(header_info['full_path']),
            'header_path': header_info['full_path'],
            'header_id': header_info.get('id'),
            'token_count': self.token_counter.count_tokens(content),
            'chunk_size': len(content)
        }
        
        # Add parent section for hierarchy
        if len(header_info['full_path']) > 1:
            metadata['parent_section'] = header_info['full_path'][0]
        
        # Add level information if found
        if level_info:
            metadata['level'] = level_info
        
        # Filter complex metadata for vector store compatibility
        return filter_complex_metadata(metadata)
    
    def chunk_rulebook(self, content: str) -> List[LangChainDocument]:
        """Enhanced chunking with progress tracking"""
        self.logger.info("🚀 Starting rulebook chunking process")
        
        # Extract headers and build hierarchy
        headers = self.parser.extract_headers(content)
        hierarchy_tree = self.parser.build_hierarchy_tree(headers)
        
        self.logger.info(f"📑 Found {len(headers)} headers in document")
        
        chunks = []
        content_lines = content.split('\n')
        
        # Process with progress bar
        with tqdm(total=len(hierarchy_tree), desc="Processing sections") as pbar:
            for i, header in enumerate(hierarchy_tree):
                try:
                    # Determine section boundaries
                    start_line = header['line_number']
                    end_line = self._find_section_end(hierarchy_tree, i, len(content_lines))
                    
                    # Extract section content
                    section_content = self.parser.get_section_content(content, start_line, end_line)
                    
                    # Skip very small sections
                    if len(section_content.strip()) < 30:
                        pbar.update(1)
                        continue
                    
                    # Check token count and split if necessary
                    token_count = self.token_counter.count_tokens(section_content)
                    
                    if token_count > self.config.max_tokens_large:
                        # Split large sections further
                        sub_chunks = self._split_large_section(section_content, header)
                        chunks.extend(sub_chunks)
                        
                        # Update progress tracker for sub-chunks
                        for chunk in sub_chunks:
                            self.progress_tracker.add_chunk(chunk, 'rulebook')
                    else:
                        # Create single chunk
                        chunk = self._create_chunk(section_content, header)
                        chunks.append(chunk)
                        self.progress_tracker.add_chunk(chunk, 'rulebook')
                    
                except Exception as e:
                    self.logger.error(f"Error processing section '{header.get('text', 'unknown')}': {e}")
                
                pbar.update(1)
        
        self.logger.info(f"✅ Created {len(chunks)} chunks from rulebook")
        return chunks
    
    def _find_section_end(self, hierarchy_tree: List[Dict], current_index: int, max_lines: int) -> int:
        """Find where current section ends"""
        current_header = hierarchy_tree[current_index]
        
        for j in range(current_index + 1, len(hierarchy_tree)):
            next_header = hierarchy_tree[j]
            if next_header['level'] <= current_header['level']:
                return next_header['line_number']
        
        return max_lines
    
    def _create_chunk(self, content: str, header_info: Dict[str, Any]) -> LangChainDocument:
        """Create a single chunk with metadata"""
        metadata = self.create_metadata(header_info, content, "dnd5rulebook.md")
        return LangChainDocument(page_content=content, metadata=metadata)
    
    def _split_large_section(self, content: str, header_info: Dict[str, Any]) -> List[LangChainDocument]:
        """Split large sections into smaller chunks"""
        # Use RecursiveCharacterTextSplitter for large sections
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.max_tokens_medium * 4,
            chunk_overlap=self.config.chunk_overlap,
            separators=["\n\n", "\n", ". ", " "]
        )
        
        splits = splitter.split_text(content)
        chunks = []
        
        for i, split in enumerate(splits):
            metadata = self.create_metadata(header_info, split, "dnd5rulebook.md")
            metadata['chunk_index'] = i
            metadata['total_chunks'] = len(splits)
            metadata['is_split'] = True
            
            doc = LangChainDocument(
                page_content=split,
                metadata=metadata
            )
            chunks.append(doc)
        
        return chunks
