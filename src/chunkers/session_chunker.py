"""
Session Notes Chunker

Processes D&D session notes into single chunks per file.
"""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from langchain.schema import Document as LangChainDocument
from langchain_community.vectorstores.utils import filter_complex_metadata

from config.settings import Config
from utils.helpers import TokenCounter


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
                
                # Filter complex metadata
                metadata = filter_complex_metadata(metadata)
                
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
