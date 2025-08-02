"""
Test suite for D&D RAG Chunker

Comprehensive tests to validate the system functionality.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import Config
from utils.helpers import TokenCounter
from chunkers.dnd_chunker import DNDRulebookChunker


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
    
    try:
        import dotenv
        print("  ✅ python-dotenv")
    except ImportError:
        print("  ❌ python-dotenv - run: pip install python-dotenv")
        return False
    
    return True


def test_files():
    """Test if required files exist"""
    print("\n📁 Testing file structure...")
    
    base_dir = Path("/Users/calvinseamons/ShadowScribe")
    
    required_files = [
        "src/config/settings.py",
        "src/chunkers/dnd_chunker.py",
        "src/chunkers/session_chunker.py",
        "src/embeddings/vector_store.py",
        "src/utils/helpers.py",
        "config.ini",
        "requirements.txt",
        "knowledge_base/dnd5rulebook.md",
        ".env"
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
        config = Config("config.ini")
        
        print(f"  ✅ Config loaded")
        print(f"  📂 Base dir: {config.base_dir}")
        print(f"  📖 Rulebook exists: {config.rulebook_file.exists()}")
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
        token_counter = TokenCounter()
        test_text = "This is a test string for token counting."
        tokens = token_counter.count_tokens(test_text)
        
        print(f"  ✅ Tokenizer working")
        print(f"  📝 Test text: '{test_text}'")
        print(f"  🔢 Token count: {tokens}")
        
        return True
    except Exception as e:
        print(f"  ❌ Tokenizer error: {e}")
        return False


def test_basic_chunking():
    """Test basic chunking functionality"""
    print("\n✂️  Testing basic chunking...")
    
    try:
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
        
        headers = chunker.parser.extract_headers(sample_content)
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
    
    try:
        config = Config("config.ini")
        api_key = config.openai_api_key
        if api_key:
            print(f"  ✅ OpenAI API key found in environment")
        else:
            print("  ⚠️  No OpenAI API key found in .env file")
        
        return True
    except Exception as e:
        print(f"  ❌ Environment test error: {e}")
        return False


def run_tests():
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
        print("1. Ensure .env file has your OPENAI_API_KEY")
        print("2. Run: python main.py --dry-run")
        print("3. Run: python main.py")
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        print("Please fix the failing tests before proceeding.")
    
    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
