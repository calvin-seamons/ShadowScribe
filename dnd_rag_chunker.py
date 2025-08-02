#!/usr/bin/env python3
"""
Comprehensive D&D 5e Content Chunker and Vector Embedder for RAG System

This script processes D&D 5e rulebook content and session notes into chunks
optimized for Retrieval-Augmented Generation (RAG) systems.

Features:
- Hierarchical markdown parsing with intelligent chunking
- Session notes processing (one chunk per file)
- Multiple vector store support (ChromaDB, FAISS)
- Configuration file support
- Progress tracking and detailed statistics
- Robust error handling and logging
- Test suite for validation

Usage:
    python dnd_rag_chunker.py [--config config.ini] [--dry-run] [--test]

Author: AI Assistant
Date: August 2025
"""

import os
import re
import json
import logging
import argparse
import configparser
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from tqdm import tqdm

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain.schema import Document as LangChainDocument
from langchain_community.vectorstores.utils import filter_complex_metadata

# For token counting
import tiktoken


class Config:
    """Enhanced configuration with file support"""
    
    def __init__(self, config_file: str = "config.ini"):
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        
        # Set defaults
        self._set_defaults()
        
        # Load from file if exists
        if os.path.exists(config_file):
            self.config.read(config_file)
            print(f"✅ Loaded configuration from {config_file}")
        else:
            print(f"⚠️  Configuration file {config_file} not found, using defaults")
    
    def _set_defaults(self):
        """Set default configuration values"""
        self.config['paths'] = {
            'base_dir': '/Users/calvinseamons/ShadowScribe',
            'knowledge_base_dir': '%(base_dir)s/knowledge_base',
            'rulebook_file': '%(knowledge_base_dir)s/dnd5rulebook.md',
            'session_notes_dir': '%(knowledge_base_dir)s/session_notes',
            'output_dir': '%(base_dir)s/vector_store',
            'chunks_output_file': '%(base_dir)s/chunks_output.json'
        }
        
        self.config['chunking'] = {
            'chunk_overlap': '150',
            'max_tokens_small': '500',
            'max_tokens_medium': '1000', 
            'max_tokens_large': '2000'
        }
        
        self.config['vectorstore'] = {
            'vector_store_type': 'chroma',
            'embedding_model': 'text-embedding-3-large',
            'collection_name': 'dnd_knowledge_base'
        }
        
        self.config['logging'] = {
            'log_level': 'INFO',
            'log_file': 'dnd_chunker.log'
        }
        
        self.config['testing'] = {
            'test_queries': 'How does rage work for barbarians?, What are the racial traits of dragonborn?, What happened with Duskryn in the last session?, How do spell slots work?, What is the Theater of Blood?'
        }
    
    # Path properties
    @property
    def base_dir(self) -> Path:
        return Path(self.config['paths']['base_dir'])
    
    @property
    def knowledge_base_dir(self) -> Path:
        return Path(self.config.get('paths', 'knowledge_base_dir', 
                                   vars=self.config['paths']))
    
    @property
    def rulebook_file(self) -> Path:
        return Path(self.config.get('paths', 'rulebook_file',
                                   vars=self.config['paths']))
    
    @property
    def session_notes_dir(self) -> Path:
        return Path(self.config.get('paths', 'session_notes_dir',
                                   vars=self.config['paths']))
    
    @property
    def output_dir(self) -> Path:
        return Path(self.config.get('paths', 'output_dir',
                                   vars=self.config['paths']))
    
    @property
    def chunks_output_file(self) -> Path:
        return Path(self.config.get('paths', 'chunks_output_file',
                                   vars=self.config['paths']))
    
    # Chunking properties
    @property
    def chunk_overlap(self) -> int:
        return self.config.getint('chunking', 'chunk_overlap')
    
    @property
    def max_tokens_small(self) -> int:
        return self.config.getint('chunking', 'max_tokens_small')
    
    @property
    def max_tokens_medium(self) -> int:
        return self.config.getint('chunking', 'max_tokens_medium')
    
    @property
    def max_tokens_large(self) -> int:
        return self.config.getint('chunking', 'max_tokens_large')
    
    # Vector store properties
    @property
    def vector_store_type(self) -> str:
        return self.config.get('vectorstore', 'vector_store_type')
    
    @property
    def embedding_model(self) -> str:
        return self.config.get('vectorstore', 'embedding_model')
    
    @property
    def openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from config or environment"""
        # First try config file
        config_key = self.config.get('vectorstore', 'openai_api_key', fallback=None)
        if config_key:
            return config_key
        
        # Fall back to environment variable
        return os.getenv('OPENAI_API_KEY')
    
    @property
    def collection_name(self) -> str:
        return self.config.get('vectorstore', 'collection_name')
    
    # Logging properties
    @property
    def log_level(self) -> str:
        return self.config.get('logging', 'log_level')
    
    @property
    def log_file(self) -> str:
        return self.config.get('logging', 'log_file')
    
    @property
    def test_queries(self) -> List[str]:
        """Parse test queries from comma-separated string"""
        try:
            queries_str = self.config.get('testing', 'test_queries', fallback='')
            if queries_str:
                return [q.strip() for q in queries_str.split(',') if q.strip()]
            return []
        except:
            return []

class TokenCounter:
    """Utility class for counting tokens"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))


class ProgressTracker:
    """Enhanced progress tracking with detailed statistics"""
    
    def __init__(self):
        self.stats = {
            'total_chunks': 0,
            'rulebook_chunks': 0,
            'session_chunks': 0,
            'chunk_types': {},
            'token_distribution': [],
            'processing_time': 0
        }
        self.start_time = datetime.now()
    
    def add_chunk(self, chunk: LangChainDocument, source_type: str):
        """Add chunk statistics"""
        self.stats['total_chunks'] += 1
        
        if source_type == 'rulebook':
            self.stats['rulebook_chunks'] += 1
        elif source_type == 'session':
            self.stats['session_chunks'] += 1
        
        chunk_type = chunk.metadata.get('type', 'unknown')
        self.stats['chunk_types'][chunk_type] = self.stats['chunk_types'].get(chunk_type, 0) + 1
        
        token_count = chunk.metadata.get('token_count', 0)
        self.stats['token_distribution'].append(token_count)
    
    def finalize(self):
        """Calculate final statistics"""
        self.stats['processing_time'] = (datetime.now() - self.start_time).total_seconds()
        
        if self.stats['token_distribution']:
            tokens = self.stats['token_distribution']
            self.stats['avg_tokens'] = sum(tokens) / len(tokens)
            self.stats['min_tokens'] = min(tokens)
            self.stats['max_tokens'] = max(tokens)
    
    def print_summary(self):
        """Print processing summary"""
        self.finalize()
        
        print("\n" + "="*60)
        print("           CHUNKING PROCESS SUMMARY")
        print("="*60)
        print(f"📊 Total chunks created: {self.stats['total_chunks']}")
        print(f"📖 Rulebook chunks: {self.stats['rulebook_chunks']}")
        print(f"📝 Session note chunks: {self.stats['session_chunks']}")
        print(f"⏱️  Processing time: {self.stats['processing_time']:.2f} seconds")
        
        if self.stats['token_distribution']:
            print(f"🔢 Average tokens per chunk: {self.stats['avg_tokens']:.0f}")
            print(f"🔢 Token range: {self.stats['min_tokens']} - {self.stats['max_tokens']}")
        
        print("\n📋 Chunk types distribution:")
        for chunk_type, count in sorted(self.stats['chunk_types'].items()):
            percentage = (count / self.stats['total_chunks']) * 100
            print(f"   {chunk_type}: {count} ({percentage:.1f}%)")


class MarkdownHierarchyParser:
    """Custom parser for hierarchical markdown content"""
    
    def __init__(self):
        self.token_counter = TokenCounter()
        self.logger = logging.getLogger(__name__)
    
    def extract_headers(self, content: str) -> List[Dict[str, Any]]:
        """Extract all headers with their hierarchy"""
        headers = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip().startswith('#'):
                try:
                    level = len(line) - len(line.lstrip('#'))
                    header_text = line.strip('#').strip()
                    
                    # Extract ID if present
                    header_id = None
                    if '{#' in header_text:
                        match = re.search(r'\{#([^}]+)\}', header_text)
                        if match:
                            header_id = match.group(1)
                            header_text = re.sub(r'\s*\{#[^}]+\}', '', header_text)
                    
                    headers.append({
                        'level': level,
                        'text': header_text.strip(),
                        'id': header_id,
                        'line_number': i,
                        'raw_line': line
                    })
                except Exception as e:
                    self.logger.warning(f"Error parsing header on line {i}: {e}")
                    continue
        
        return headers
    
    def get_section_content(self, content: str, start_line: int, end_line: Optional[int] = None) -> str:
        """Extract content between line numbers"""
        lines = content.split('\n')
        if end_line is None:
            end_line = len(lines)
        
        return '\n'.join(lines[start_line:end_line])
    
    def build_hierarchy_tree(self, headers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build a hierarchical tree from headers"""
        stack = []
        
        for header in headers:
            # Pop from stack until we find the correct parent level
            while stack and stack[-1]['level'] >= header['level']:
                stack.pop()
            
            # Add parent references
            parent_headers = [h['text'] for h in stack]
            header['parent_headers'] = parent_headers
            header['full_path'] = parent_headers + [header['text']]
            
            # Add to stack
            stack.append(header)
        
        return headers


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
            'headers': ' > '.join(header_info['full_path']),  # Convert list to string
            'header_path': header_info['full_path'],  # Keep original for processing
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
            chunk_size=self.config.max_tokens_medium * 4,  # Rough character estimate
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


class SessionNotesChunker:
    """Chunker for D&D session notes"""
    
    def __init__(self, config: Config):
        self.config = config
        self.token_counter = TokenCounter()
        self.logger = logging.getLogger(__name__)
    
    def extract_date_from_filename(self, filename: str) -> Optional[str]:
        """Extract date from session note filename"""
        # Pattern for MM-DD-YY format
        match = re.search(r'(\d{2}-\d{2}-\d{2})', filename)
        if match:
            date_str = match.group(1)
            try:
                # Convert to proper date format (assuming 20XX for YY)
                date_obj = datetime.strptime(date_str, "%m-%d-%y")
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                pass
        
        return None
    
    def chunk_session_notes(self, session_notes_dir: Path) -> List[LangChainDocument]:
        """Process all session note files"""
        self.logger.info(f"📝 Processing session notes from {session_notes_dir}")
        
        chunks = []
        
        if not session_notes_dir.exists():
            self.logger.warning(f"Session notes directory not found: {session_notes_dir}")
            return chunks
        
        # Process each markdown file in the session notes directory
        for file_path in session_notes_dir.glob("*.md"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract date from filename
                date = self.extract_date_from_filename(file_path.name)
                
                # Create metadata
                metadata = {
                    'source': file_path.name,
                    'type': 'session_note',
                    'date': date,
                    'filename': file_path.name,
                    'token_count': self.token_counter.count_tokens(content),
                    'chunk_size': len(content)
                }
                
                # Create document (entire session as one chunk)
                doc = LangChainDocument(
                    page_content=content,
                    metadata=metadata
                )
                chunks.append(doc)
                
                self.logger.info(f"Processed session note: {file_path.name}")
                
            except Exception as e:
                self.logger.error(f"Error processing {file_path}: {e}")
        
        self.logger.info(f"✅ Created {len(chunks)} session note chunks")
        return chunks


class VectorStoreManager:
    """Manages vector store operations"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Set up OpenAI API key
        api_key = config.openai_api_key
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key
        elif not os.getenv('OPENAI_API_KEY'):
            self.logger.warning("No OpenAI API key found in config or environment")
        
        self.embeddings = OpenAIEmbeddings(model=config.embedding_model)
    
    def create_vector_store(self, chunks: List[LangChainDocument]) -> Any:
        """Create and populate vector store with batch processing"""
        self.logger.info(f"🔮 Creating {self.config.vector_store_type} vector store with {len(chunks)} chunks")
        
        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate batch size to stay under token limit
        batch_size = self._calculate_batch_size(chunks)
        self.logger.info(f"📦 Processing in batches of {batch_size} chunks")
        
        if self.config.vector_store_type.lower() == "chroma":
            vector_store = self._create_chroma_batched(chunks, batch_size)
            
        elif self.config.vector_store_type.lower() == "faiss":
            vector_store = self._create_faiss_batched(chunks, batch_size)
        
        else:
            raise ValueError(f"Unsupported vector store type: {self.config.vector_store_type}")
        
        self.logger.info("✅ Vector store created successfully")
        return vector_store
    
    def _calculate_batch_size(self, chunks: List[LangChainDocument]) -> int:
        """Calculate optimal batch size to stay under OpenAI token limits"""
        # OpenAI embedding limit is 300,000 tokens per request
        # Use a safety margin of 250,000 tokens
        token_limit = 250000
        
        # Calculate average tokens per chunk
        total_tokens = sum(chunk.metadata.get('token_count', 0) for chunk in chunks[:100])  # Sample first 100
        avg_tokens = total_tokens / min(100, len(chunks))
        
        # Calculate batch size
        if avg_tokens > 0:
            batch_size = max(1, int(token_limit / avg_tokens))
        else:
            batch_size = 50  # Default fallback
        
        # Cap at reasonable limits
        batch_size = min(batch_size, 200)  # Don't make batches too large
        batch_size = max(batch_size, 10)   # Don't make batches too small
        
        self.logger.info(f"📊 Average tokens per chunk: {avg_tokens:.0f}, using batch size: {batch_size}")
        return batch_size
    
    def _create_chroma_batched(self, chunks: List[LangChainDocument], batch_size: int) -> Any:
        """Create ChromaDB vector store with batched processing"""
        vector_store = None
        
        # Filter complex metadata from all chunks
        filtered_chunks = []
        for chunk in chunks:
            # Create a copy of the chunk with filtered metadata
            filtered_chunk = LangChainDocument(
                page_content=chunk.page_content,
                metadata=self._filter_metadata_for_chroma(chunk.metadata)
            )
            filtered_chunks.append(filtered_chunk)
        
        # Process in batches with progress bar
        with tqdm(total=len(filtered_chunks), desc="Creating embeddings") as pbar:
            for i in range(0, len(filtered_chunks), batch_size):
                batch = filtered_chunks[i:i + batch_size]
                
                try:
                    if vector_store is None:
                        # Create initial vector store with first batch
                        vector_store = Chroma.from_documents(
                            documents=batch,
                            embedding=self.embeddings,
                            persist_directory=str(self.config.output_dir),
                            collection_name=self.config.collection_name
                        )
                    else:
                        # Add subsequent batches
                        vector_store.add_documents(batch)
                    
                    pbar.update(len(batch))
                    
                except Exception as e:
                    self.logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                    # If batch fails, try smaller chunks
                    if len(batch) > 1:
                        self.logger.info("Retrying with smaller batch size...")
                        for doc in batch:
                            try:
                                if vector_store is None:
                                    vector_store = Chroma.from_documents(
                                        documents=[doc],
                                        embedding=self.embeddings,
                                        persist_directory=str(self.config.output_dir),
                                        collection_name=self.config.collection_name
                                    )
                                else:
                                    vector_store.add_documents([doc])
                                pbar.update(1)
                            except Exception as doc_error:
                                self.logger.error(f"Failed to process individual document: {doc_error}")
                                pbar.update(1)
                    else:
                        self.logger.error(f"Failed to process single document, skipping...")
                        pbar.update(len(batch))
        
        if vector_store:
            vector_store.persist()
        
        return vector_store
    
    def _filter_metadata_for_chroma(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Filter metadata to only include types supported by ChromaDB"""
        filtered = {}
        for key, value in metadata.items():
            # Only keep simple types that ChromaDB supports
            if isinstance(value, (str, int, float, bool)) or value is None:
                filtered[key] = value
            elif isinstance(value, list):
                # Convert lists to strings
                if key == 'header_path':
                    # Skip the header_path list, we already have 'headers' as string
                    continue
                else:
                    # Convert other lists to comma-separated strings
                    filtered[key] = ', '.join(str(item) for item in value)
            else:
                # Convert other types to strings
                filtered[key] = str(value)
        
        return filtered
    
    def _create_faiss_batched(self, chunks: List[LangChainDocument], batch_size: int) -> Any:
        """Create FAISS vector store with batched processing"""
        vector_store = None
        
        # Filter complex metadata from all chunks
        filtered_chunks = []
        for chunk in chunks:
            # Create a copy of the chunk with filtered metadata
            filtered_chunk = LangChainDocument(
                page_content=chunk.page_content,
                metadata=self._filter_metadata_for_faiss(chunk.metadata)
            )
            filtered_chunks.append(filtered_chunk)
        
        # Process in batches with progress bar
        with tqdm(total=len(filtered_chunks), desc="Creating embeddings") as pbar:
            for i in range(0, len(filtered_chunks), batch_size):
                batch = filtered_chunks[i:i + batch_size]
                
                try:
                    if vector_store is None:
                        # Create initial vector store with first batch
                        vector_store = FAISS.from_documents(
                            documents=batch,
                            embedding=self.embeddings
                        )
                    else:
                        # Create temporary store for batch and merge
                        temp_store = FAISS.from_documents(
                            documents=batch,
                            embedding=self.embeddings
                        )
                        vector_store.merge_from(temp_store)
                    
                    pbar.update(len(batch))
                    
                except Exception as e:
                    self.logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                    # If batch fails, try individual documents
                    if len(batch) > 1:
                        self.logger.info("Retrying with individual documents...")
                        for doc in batch:
                            try:
                                if vector_store is None:
                                    vector_store = FAISS.from_documents(
                                        documents=[doc],
                                        embedding=self.embeddings
                                    )
                                else:
                                    temp_store = FAISS.from_documents(
                                        documents=[doc],
                                        embedding=self.embeddings
                                    )
                                    vector_store.merge_from(temp_store)
                                pbar.update(1)
                            except Exception as doc_error:
                                self.logger.error(f"Failed to process individual document: {doc_error}")
                                pbar.update(1)
                    else:
                        self.logger.error(f"Failed to process single document, skipping...")
                        pbar.update(len(batch))
        
        if vector_store:
            vector_store.save_local(str(self.config.output_dir))
        
        return vector_store
    
    def _filter_metadata_for_faiss(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Filter metadata for FAISS compatibility"""
        filtered = {}
        for key, value in metadata.items():
            # FAISS is more flexible than Chroma but still prefer simple types
            if isinstance(value, (str, int, float, bool)) or value is None:
                filtered[key] = value
            elif isinstance(value, list):
                # Convert lists to strings
                if key == 'header_path':
                    # Skip the header_path list, we already have 'headers' as string
                    continue
                else:
                    # Convert other lists to comma-separated strings
                    filtered[key] = ', '.join(str(item) for item in value)
            else:
                # Convert other types to strings
                filtered[key] = str(value)
        
        return filtered
    
    def load_vector_store(self) -> Any:
        """Load existing vector store"""
        if self.config.vector_store_type.lower() == "chroma":
            return Chroma(
                persist_directory=str(self.config.output_dir),
                embedding_function=self.embeddings,
                collection_name=self.config.collection_name
            )
        elif self.config.vector_store_type.lower() == "faiss":
            return FAISS.load_local(str(self.config.output_dir), self.embeddings)
        else:
            raise ValueError(f"Unsupported vector store type: {self.config.vector_store_type}")


def setup_logging(config: Config):
    """Setup enhanced logging with file and console output"""
    log_level = getattr(logging, config.log_level.upper())
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Setup file handler
    file_handler = logging.FileHandler(config.log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def save_chunks_to_json(chunks: List[LangChainDocument], output_file: Path, format_type: str = 'json'):
    """Save chunks to JSON or CSV file for inspection"""
    if format_type == 'json':
        chunks_data = []
        for chunk in chunks:
            chunk_data = {
                'content': chunk.page_content[:500] + "..." if len(chunk.page_content) > 500 else chunk.page_content,
                'content_length': len(chunk.page_content),
                'metadata': chunk.metadata
            }
            chunks_data.append(chunk_data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)
    
    elif format_type == 'csv':
        try:
            import pandas as pd
            
            rows = []
            for chunk in chunks:
                row = {
                    'content_preview': chunk.page_content[:200] + "..." if len(chunk.page_content) > 200 else chunk.page_content,
                    'content_length': len(chunk.page_content),
                    **chunk.metadata
                }
                rows.append(row)
            
            df = pd.DataFrame(rows)
            csv_file = output_file.with_suffix('.csv')
            df.to_csv(csv_file, index=False)
            
        except ImportError:
            logging.warning("pandas not available, falling back to JSON format")
            save_chunks_to_json(chunks, output_file, 'json')
    
    logging.info(f"💾 Saved {len(chunks)} chunks to {output_file}")


def test_retrieval(vector_store: Any, test_queries: List[str]):
    """Test retrieval with sample queries"""
    logger = logging.getLogger(__name__)
    logger.info("🔍 Testing retrieval system")
    
    for query in test_queries:
        logger.info(f"\nQuery: {query}")
        
        try:
            # Perform similarity search
            results = vector_store.similarity_search(query, k=3)
            
            for i, result in enumerate(results, 1):
                logger.info(f"Result {i}:")
                logger.info(f"  Type: {result.metadata.get('type', 'unknown')}")
                logger.info(f"  Source: {result.metadata.get('source', 'unknown')}")
                logger.info(f"  Name: {result.metadata.get('name', 'unknown')}")
                logger.info(f"  Content preview: {result.page_content[:200]}...")
        except Exception as e:
            logger.error(f"Error testing query '{query}': {e}")


def run_tests():
    """Run comprehensive test suite"""
    print("🧪 D&D RAG Chunker Test Suite")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Imports
    total_tests += 1
    print("🔍 Testing imports...")
    try:
        import langchain
        import tiktoken
        import tqdm
        import chromadb
        print("  ✅ All imports successful")
        tests_passed += 1
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
    
    # Test 2: Configuration
    total_tests += 1
    print("\n⚙️  Testing configuration...")
    try:
        config = Config("config.ini")
        print(f"  ✅ Config loaded")
        print(f"  📂 Base dir: {config.base_dir}")
        print(f"  📖 Rulebook exists: {config.rulebook_file.exists()}")
        print(f"  🧠 Vector store: {config.vector_store_type}")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ Config error: {e}")
    
    # Test 3: Token counting
    total_tests += 1
    print("\n🔤 Testing tokenizer...")
    try:
        token_counter = TokenCounter()
        test_text = "This is a test string for token counting."
        tokens = token_counter.count_tokens(test_text)
        print(f"  ✅ Tokenizer working (tokens: {tokens})")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ Tokenizer error: {e}")
    
    # Test 4: Environment
    total_tests += 1
    print("\n🌍 Testing environment...")
    try:
        config = Config("config.ini")
        api_key = config.openai_api_key
        if api_key:
            print(f"  ✅ OpenAI API key found in configuration")
            tests_passed += 1
        else:
            print("  ⚠️  No OpenAI API key found in config or environment")
    except:
        print("  ⚠️  Could not check API key configuration")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! System ready to use.")
    else:
        print("⚠️  Some tests failed. Please fix issues before proceeding.")
    
    return tests_passed == total_tests


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='D&D RAG Content Chunker')
    parser.add_argument('--config', default='config.ini', 
                       help='Configuration file path')
    parser.add_argument('--dry-run', action='store_true',
                       help='Process content without creating vector store')
    parser.add_argument('--output-format', choices=['json', 'csv'], default='json',
                       help='Output format for chunk inspection')
    parser.add_argument('--test', action='store_true',
                       help='Run test suite and exit')
    
    args = parser.parse_args()
    
    # Run tests if requested
    if args.test:
        success = run_tests()
        return 0 if success else 1
    
    # Load configuration
    config = Config(args.config)
    
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting D&D RAG Chunking Process")
    
    try:
        # Validate environment
        api_key = config.openai_api_key
        if not api_key and not args.dry_run:
            logger.warning("⚠️  No OpenAI API key found in config or environment. Set it for embedding generation.")
        elif api_key:
            logger.info("✅ OpenAI API key loaded from configuration")
        
        # Validate paths
        if not config.rulebook_file.exists():
            raise FileNotFoundError(f"📖 Rulebook not found: {config.rulebook_file}")
        
        # Initialize chunkers
        rulebook_chunker = DNDRulebookChunker(config)
        session_chunker = SessionNotesChunker(config)
        
        # Process rulebook
        logger.info("📖 Processing D&D 5e Rulebook")
        with open(config.rulebook_file, 'r', encoding='utf-8') as f:
            rulebook_content = f.read()
        
        rulebook_chunks = rulebook_chunker.chunk_rulebook(rulebook_content)
        
        # Process session notes
        logger.info("📝 Processing Session Notes")
        session_chunks = session_chunker.chunk_session_notes(config.session_notes_dir)
        
        # Add session chunks to progress tracker
        for chunk in session_chunks:
            rulebook_chunker.progress_tracker.add_chunk(chunk, 'session')
        
        # Combine all chunks
        all_chunks = rulebook_chunks + session_chunks
        logger.info(f"📊 Total chunks created: {len(all_chunks)}")
        
        # Save chunks to file for inspection
        save_chunks_to_json(all_chunks, config.chunks_output_file, args.output_format)
        
        # Print summary
        rulebook_chunker.progress_tracker.print_summary()
        
        if not args.dry_run:
            # Create vector store
            vector_store_manager = VectorStoreManager(config)
            vector_store = vector_store_manager.create_vector_store(all_chunks)
            
            # Test retrieval
            if config.test_queries:
                test_retrieval(vector_store, config.test_queries)
            
            logger.info(f"✅ Vector store saved to: {config.output_dir}")
        else:
            logger.info("🔍 Dry run completed - no vector store created")
        
        logger.info("🎉 D&D RAG Chunking Process completed successfully!")
        logger.info(f"📄 Chunks inspection file: {config.chunks_output_file}")
        
    except Exception as e:
        logger.error(f"❌ Error in main process: {e}")
        raise


if __name__ == "__main__":
    main()
