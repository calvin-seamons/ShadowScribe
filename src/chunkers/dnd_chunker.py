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
        # return filter_complex_metadata(metadata)
        # Temporarily skip filtering to isolate the issue
        return metadata
    
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
                        
                        # Validate all sub_chunks are proper Document objects
                        valid_sub_chunks = []
                        for j, sub_chunk in enumerate(sub_chunks):
                            if isinstance(sub_chunk, LangChainDocument):
                                valid_sub_chunks.append(sub_chunk)
                                self.progress_tracker.add_chunk(sub_chunk, 'rulebook')
                            else:
                                self.logger.error(f"Sub-chunk {j} is not LangChainDocument: {type(sub_chunk)}")
                        
                        chunks.extend(valid_sub_chunks)
                    else:
                        # Create single chunk
                        chunk = self._create_chunk(section_content, header)
                        
                        # Validate chunk is proper Document object
                        if isinstance(chunk, LangChainDocument):
                            chunks.append(chunk)
                            self.progress_tracker.add_chunk(chunk, 'rulebook')
                        else:
                            self.logger.error(f"Created chunk is not LangChainDocument: {type(chunk)}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing section '{header.get('text', 'unknown')}': {e}")
                    # Add more detailed error info for debugging
                    import traceback
                    self.logger.debug(f"Full error traceback: {traceback.format_exc()}")
                
                pbar.update(1)
        
        self.logger.info(f"✅ Created {len(chunks)} chunks from rulebook")
        
        # Debug: Check chunk types
        for i, chunk in enumerate(chunks[:5]):  # Check first 5 chunks
            self.logger.debug(f"Chunk {i}: type={type(chunk)}, has_metadata={hasattr(chunk, 'metadata')}")
        
        # Final validation: Remove any non-Document objects that might have slipped through
        valid_chunks = []
        invalid_count = 0
        for i, chunk in enumerate(chunks):
            if isinstance(chunk, LangChainDocument):
                valid_chunks.append(chunk)
            else:
                invalid_count += 1
                self.logger.error(f"Removing invalid chunk {i}: type={type(chunk)}")
        
        if invalid_count > 0:
            self.logger.warning(f"Removed {invalid_count} invalid chunks from final list")
            
        return valid_chunks
    
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
        try:
            metadata = self.create_metadata(header_info, content, "dnd5rulebook.md")
            return LangChainDocument(page_content=content, metadata=metadata)
        except Exception as e:
            self.logger.error(f"Error in _create_chunk: {e}")
            raise
    
    def _split_large_section(self, content: str, header_info: Dict[str, Any]) -> List[LangChainDocument]:
        """Split large sections into smaller chunks"""
        # Use RecursiveCharacterTextSplitter for large sections
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.max_tokens_medium * 4,
            chunk_overlap=self.config.chunk_overlap,
            separators=["\n\n", "\n", ". ", " "]
        )
        
        try:
            splits = splitter.split_text(content)
            chunks = []
            
            # Debug logging
            self.logger.debug(f"Splitter returned {len(splits)} splits")
            if splits:
                self.logger.debug(f"First split type: {type(splits[0])}")
            
            for i, split in enumerate(splits):
                # Ensure split is a string
                if not isinstance(split, str):
                    self.logger.warning(f"Split {i} is not a string: {type(split)}, converting...")
                    split = str(split)
                
                # Skip empty splits
                if not split.strip():
                    self.logger.debug(f"Skipping empty split {i}")
                    continue
                    
                try:
                    metadata = self.create_metadata(header_info, split, "dnd5rulebook.md")
                    metadata['chunk_index'] = i
                    metadata['total_chunks'] = len(splits)
                    metadata['is_split'] = True
                    
                    doc = LangChainDocument(
                        page_content=split,
                        metadata=metadata
                    )
                    
                    # Verify the document was created correctly
                    if not isinstance(doc, LangChainDocument):
                        self.logger.error(f"Failed to create LangChainDocument for split {i}")
                        continue
                        
                    chunks.append(doc)
                    
                except Exception as e:
                    self.logger.error(f"Error creating document for split {i}: {e}")
                    continue
            
            self.logger.debug(f"Successfully created {len(chunks)} documents from {len(splits)} splits")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error in _split_large_section: {e}")
            import traceback
            self.logger.debug(f"Full traceback: {traceback.format_exc()}")
            
            # Fallback: create a single chunk
            try:
                metadata = self.create_metadata(header_info, content, "dnd5rulebook.md")
                metadata['is_split'] = False
                doc = LangChainDocument(page_content=content, metadata=metadata)
                return [doc]
            except Exception as fallback_error:
                self.logger.error(f"Even fallback failed: {fallback_error}")
                return []
