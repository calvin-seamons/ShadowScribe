"""
Configuration management for D&D RAG Chunker

Handles loading configuration from INI files and environment variables.
"""

import os
import configparser
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv


class Config:
    """Enhanced configuration with file and environment variable support"""
    
    def __init__(self, config_file: str = "config.ini"):
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        
        # Load environment variables from .env file
        load_dotenv()
        
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
        """Get OpenAI API key from environment variables"""
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
