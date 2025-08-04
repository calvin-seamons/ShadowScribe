"""
Utility classes for token counting and progress tracking
"""

import tiktoken
from datetime import datetime
from typing import Dict, Any, List
from langchain.schema import Document as LangChainDocument


class TokenCounter:
    """Utility class for counting tokens"""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
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
        # Add type checking to prevent errors
        if not hasattr(chunk, 'metadata'):
            print(f"WARNING: Invalid chunk object passed to add_chunk: {type(chunk)}")
            return
            
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
