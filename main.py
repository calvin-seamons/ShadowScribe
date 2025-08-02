#!/usr/bin/env python3
"""
D&D 5e RAG Chunker - Main Application

Modular D&D 5e content chunker and vector embedder for RAG systems.

Usage:
    python main.py [--config config.ini] [--dry-run] [--test]

Author: AI Assistant
Date: August 2025
"""

import sys
import argparse
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from config.settings import Config
from utils.logging_config import setup_logging
from utils.file_io import save_chunks_to_json
from chunkers.dnd_chunker import DNDRulebookChunker
from chunkers.session_chunker import SessionNotesChunker
from embeddings.vector_store import VectorStoreManager, test_retrieval
from tests.test_suite import run_tests

import logging


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
            logger.warning("⚠️  No OpenAI API key found in .env file. Set it for embedding generation.")
        elif api_key:
            logger.info("✅ OpenAI API key loaded from environment")
        
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
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error in main process: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
