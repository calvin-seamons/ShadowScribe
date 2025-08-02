#!/usr/bin/env python3
"""
Test script for D&D RAG Chunker

This script validates the setup and performs basic functionality tests.

Usage: python test_chunker.py
"""

import os
import sys
from pathlib import Path

def test_imports():
    """Test if all required packages can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import langchain
        print("  ✅ LangChain")
    except ImportError:
        print("  ❌ LangChain - run: pip install langchain")
        return False
    
    try:
        import tiktoken
        print("  ✅ tiktoken")
    except ImportError:
        print("  ❌ tiktoken - run: pip install tiktoken")
        return False
    
    try:
        import tqdm
        print("  ✅ tqdm")
    except ImportError:
        print("  ❌ tqdm - run: pip install tqdm")
        return False
    
    try:
        import chromadb
        print("  ✅ ChromaDB")
    except ImportError:
        print("  ❌ ChromaDB - run: pip install chromadb")
        return False
    
    return True

def test_files():
    """Test if required files exist"""
    print("\n📁 Testing file structure...")
    
    base_dir = Path("/Users/calvinseamons/ShadowScribe")
    
    required_files = [
        "dnd_rag_chunker.py",
        "dnd_rag_chunker_enhanced.py", 
        "config.ini",
        "requirements.txt",
        "knowledge_base/dnd5rulebook.md"
    ]
    
    all_good = True
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - File missing!")
            all_good = False
    
    # Check session notes directory
    session_dir = base_dir / "knowledge_base/session_notes"
    if session_dir.exists():
        session_files = list(session_dir.glob("*.md"))
        print(f"  ✅ session_notes/ ({len(session_files)} files)")
    else:
        print("  ⚠️  session_notes/ directory missing")
    
    return all_good

def test_config():
    """Test configuration loading"""
    print("\n⚙️  Testing configuration...")
    
    try:
        from dnd_rag_chunker import Config
        config = Config("config.ini")
        
        print(f"  ✅ Config loaded")
        print(f"  📂 Base dir: {config.base_dir}")
        print(f"  📖 Rulebook: {config.rulebook_file.exists()}")
        print(f"  🧠 Vector store: {config.vector_store_type}")
        print(f"  🔢 Max tokens (medium): {config.max_tokens_medium}")
        
        return True
    except Exception as e:
        print(f"  ❌ Config error: {e}")
        return False

def test_tokenizer():
    """Test token counting"""
    print("\n🔤 Testing tokenizer...")
    
    try:
        import tiktoken
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        
        test_text = "This is a test string for token counting."
        tokens = encoding.encode(test_text)
        
        print(f"  ✅ Tokenizer working")
        print(f"  📝 Test text: '{test_text}'")
        print(f"  🔢 Token count: {len(tokens)}")
        
        return True
    except Exception as e:
        print(f"  ❌ Tokenizer error: {e}")
        return False

def test_basic_chunking():
    """Test basic chunking functionality"""
    print("\n✂️  Testing basic chunking...")
    
    try:
        from dnd_rag_chunker import Config, DNDRulebookChunker
        
        config = Config("config.ini")
        chunker = DNDRulebookChunker(config)
        
        # Test with sample markdown
        sample_content = """# Test Chapter

## Section 1

### Feature A
This is a test feature with some content.

### Feature B  
This is another test feature.

## Section 2

### Feature C
Yet another feature for testing."""
        
        headers = chunker.extract_headers(sample_content)
        print(f"  ✅ Header extraction: {len(headers)} headers found")
        
        # Test content type detection
        content_type = chunker.determine_content_type(["Test", "Feature A"], "Test content")
        print(f"  ✅ Content type detection: {content_type}")
        
        return True
    except Exception as e:
        print(f"  ❌ Chunking test error: {e}")
        return False

def test_environment():
    """Test environment variables"""
    print("\n🌍 Testing environment...")
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print(f"  ✅ OPENAI_API_KEY set (length: {len(openai_key)})")
    else:
        print("  ⚠️  OPENAI_API_KEY not set (required for embeddings)")
    
    return True

def main():
    """Run all tests"""
    print("🧪 D&D RAG Chunker Test Suite")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_files,
        test_config,
        test_tokenizer,
        test_basic_chunking,
        test_environment
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        print("\n✨ Your D&D RAG Chunker is ready to use!")
        print("\nNext steps:")
        print("1. Set OPENAI_API_KEY if not already set")
        print("2. Run: python dnd_rag_chunker_enhanced.py --dry-run")
        print("3. Run: python dnd_rag_chunker_enhanced.py")
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        print("Please fix the failing tests before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
