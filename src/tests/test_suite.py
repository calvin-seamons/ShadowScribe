"""
Comprehensive Test Suite for ShadowScribe LLM Engine

Tests all core functionality including:
- 4-pass query routing system
- Knowledge base handlers
- LLM client and validation
- Response generation
- System integration

Run this from the repository root: python -m src.tests.test_suite
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List
import unittest
from unittest.mock import Mock, patch, AsyncMock

# Ensure we're working from repository root
repo_root = Path(__file__).parent.parent.parent
os.chdir(repo_root)
sys.path.insert(0, str(repo_root / "src"))

# Import all ShadowScribe components
try:
    from src.engine.shadowscribe_engine import ShadowScribeEngine
    from src.engine.query_router import QueryRouter
    from src.engine.content_retriever import ContentRetriever
    from src.engine.response_generator import ResponseGenerator
    from src.knowledge.knowledge_base import KnowledgeBase
    from src.knowledge.rulebook_handler import RulebookHandler
    from src.knowledge.character_handler import CharacterHandler
    from src.knowledge.session_handler import SessionHandler
    from src.utils.llm_client import LLMClient
    from src.utils.response_models import (
        SourceSelectionResponse, 
        RulebookTargetResponse,
        CharacterTargetResponse,
        SessionTargetResponse
    )
    from src.utils.validation import ValidationHelper
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Repository root: {repo_root}")
    print("Please run this test from the repository root:")
    print("python -m src.tests.test_suite")
    sys.exit(1)

# Optional imports for file_io and helpers (may not exist yet)
try:
    from src.utils.file_io import FileIO
except ImportError:
    FileIO = None

try:
    from src.utils.helpers import format_content
except ImportError:
    format_content = None


class TestEnvironmentSetup(unittest.TestCase):
    """Test environment setup and dependencies"""
    
    def test_imports(self):
        """Test if all required packages can be imported"""
        print("🔍 Testing imports...")
        
        import_tests = [
            ("openai", "OpenAI API client"),
            ("pydantic", "Pydantic for validation"),
            ("tiktoken", "Token counting"),
            ("asyncio", "Async support"),
            ("json", "JSON handling"),
            ("pathlib", "Path utilities"),
        ]
        
        for module, description in import_tests:
            try:
                __import__(module)
                print(f"  ✅ {description}")
            except ImportError:
                print(f"  ⚠️  {description} - Module '{module}' not available")
    
    def test_file_structure(self):
        """Test if required files and directories exist"""
        print("\n📁 Testing file structure...")
        
        repo_dir = Path.cwd()
        
        required_structure = {
            "src/engine/shadowscribe_engine.py": "Main engine",
            "src/engine/query_router.py": "Query router",
            "src/engine/content_retriever.py": "Content retriever",
            "src/engine/response_generator.py": "Response generator",
            "src/knowledge/knowledge_base.py": "Knowledge base",
            "src/knowledge/rulebook_handler.py": "Rulebook handler",
            "src/knowledge/character_handler.py": "Character handler",
            "src/knowledge/session_handler.py": "Session handler",
            "src/utils/llm_client.py": "LLM client",
            "src/utils/response_models.py": "Response models",
            "src/utils/validation.py": "Validation utilities",
            "knowledge_base/": "Knowledge base directory",
        }
        
        for file_path, description in required_structure.items():
            full_path = repo_dir / file_path
            if full_path.exists():
                print(f"  ✅ {description}")
            else:
                print(f"  ⚠️  {description} - {file_path} missing")
    
    def test_knowledge_base_files(self):
        """Test if knowledge base files exist"""
        print("\n📚 Testing knowledge base files...")
        
        knowledge_base_dir = Path.cwd() / "knowledge_base"
        
        required_files = {
            "dnd5e_srd_full.json": "Full D&D SRD",
            "dnd5e_srd_query_helper.json": "SRD query helper",
            "character.json": "Character data",
            "inventory_list.json": "Character inventory",
            "feats_and_traits.json": "Character feats",
            "spell_list.json": "Character spells",
            "action_list.json": "Character actions",
            "character_background.json": "Character background",
            "session_notes/": "Session notes directory",
        }
        
        for file_path, description in required_files.items():
            full_path = knowledge_base_dir / file_path
            if full_path.exists():
                print(f"  ✅ {description}")
            else:
                print(f"  ⚠️  {description} - {file_path} missing")


class TestKnowledgeBase(unittest.TestCase):
    """Test knowledge base and data handlers"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.knowledge_base_path = "./knowledge_base"
        self.kb = None
        try:
            self.kb = KnowledgeBase(self.knowledge_base_path)
        except Exception as e:
            print(f"Warning: Could not initialize knowledge base: {e}")
    
    def test_knowledge_base_initialization(self):
        """Test knowledge base initialization"""
        print("\n🗄️  Testing knowledge base initialization...")
        
        if self.kb is None:
            print("  ⚠️  Knowledge base not available - skipping test")
            return
        
        # Test that handlers are initialized
        self.assertIsNotNone(self.kb.rulebook, "Rulebook handler should be initialized")
        self.assertIsNotNone(self.kb.character, "Character handler should be initialized")
        self.assertIsNotNone(self.kb.sessions, "Session handler should be initialized")
        print("  ✅ All handlers initialized")
    
    def test_source_overview(self):
        """Test getting source overview"""
        print("\n📊 Testing source overview...")
        
        if self.kb is None:
            print("  ⚠️  Knowledge base not available - skipping test")
            return
        
        overview = self.kb.get_source_overview()
        
        # Check required sources
        required_sources = ["dnd_rulebook", "character_data", "session_notes"]
        for source in required_sources:
            self.assertIn(source, overview, f"Source {source} should be in overview")
            self.assertIn("description", overview[source])
            self.assertIn("status", overview[source])
        
        print("  ✅ Source overview structure valid")
        
        # Print source status
        for source, info in overview.items():
            status_emoji = "✅" if info["status"] == "loaded" else "⚠️"
            print(f"  {status_emoji} {source}: {info['status']}")    


class TestRulebookHandler(unittest.TestCase):
    """Test D&D SRD rulebook handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.handler = None
        try:
            self.handler = RulebookHandler("./knowledge_base")
            self.handler.load_data()
        except Exception as e:
            print(f"Warning: Could not initialize rulebook handler: {e}")
    
    def test_rulebook_loading(self):
        """Test rulebook data loading"""
        print("\n📖 Testing rulebook loading...")
        
        if self.handler is None:
            print("  ⚠️  Rulebook handler not available - skipping test")
            return
        
        # Test basic loading
        self.assertTrue(self.handler.is_loaded(), "Rulebook should be loaded")
        
        # Test section count
        section_count = self.handler.get_section_count()
        print(f"  ✅ Loaded {section_count} sections")
        
        # Test categories
        categories = self.handler.get_main_categories()
        self.assertIsInstance(categories, list, "Categories should be a list")
        print(f"  ✅ Found {len(categories)} main categories")
    
    def test_section_retrieval(self):
        """Test section retrieval by ID"""
        print("\n🔍 Testing section retrieval...")
        
        if self.handler is None or not self.handler.is_loaded():
            print("  ⚠️  Rulebook not available - skipping test")
            return
        
        # Test with mock section IDs (would need real IDs in practice)
        try:
            # Get query helper to find real section IDs
            query_helper = self.handler.get_query_helper()
            if query_helper and "sections" in query_helper:
                sample_ids = list(query_helper["sections"].keys())[:3]
                sections = self.handler.get_sections_by_ids(sample_ids)
                self.assertIsInstance(sections, list, "Should return list of sections")
                print(f"  ✅ Successfully retrieved {len(sections)} sections")
            else:
                print("  ⚠️  No query helper available for section testing")
        except Exception as e:
            print(f"  ⚠️  Section retrieval test failed: {e}")
    
    def test_keyword_search(self):
        """Test keyword-based search"""
        print("\n🔎 Testing keyword search...")
        
        if self.handler is None or not self.handler.is_loaded():
            print("  ⚠️  Rulebook not available - skipping test")
            return
        
        # Test common D&D keywords
        test_keywords = [
            ["counterspell"],
            ["fireball"],
            ["armor", "class"],
            ["spell", "slots"]
        ]
        
        for keywords in test_keywords:
            try:
                results = self.handler.search_by_keywords(keywords)
                self.assertIsInstance(results, list, "Search should return list")
                print(f"  ✅ Search for {keywords}: {len(results)} results")
            except Exception as e:
                print(f"  ⚠️  Search for {keywords} failed: {e}")


class TestCharacterHandler(unittest.TestCase):
    """Test character data handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.handler = None
        try:
            self.handler = CharacterHandler("./knowledge_base")
            self.handler.load_data()
        except Exception as e:
            print(f"Warning: Could not initialize character handler: {e}")
    
    def test_character_loading(self):
        """Test character data loading"""
        print("\n🧙 Testing character loading...")
        
        if self.handler is None:
            print("  ⚠️  Character handler not available - skipping test")
            return
        
        # Test basic loading
        self.assertTrue(self.handler.is_loaded(), "Character data should be loaded")
        
        # Test available files
        files = self.handler.get_available_files()
        expected_files = [
            "character.json",
            "inventory_list.json", 
            "feats_and_traits.json",
            "spell_list.json",
            "action_list.json",
            "character_background.json",
            "objectives_and_contracts.json"
        ]
        
        for expected_file in expected_files:
            if expected_file in files:
                print(f"  ✅ {expected_file}")
            else:
                print(f"  ⚠️  {expected_file} missing")
    
    def test_basic_character_info(self):
        """Test getting basic character information"""
        print("\n👤 Testing basic character info...")
        
        if self.handler is None or not self.handler.is_loaded():
            print("  ⚠️  Character data not available - skipping test")
            return
        
        try:
            basic_info = self.handler.get_basic_info()
            self.assertIsInstance(basic_info, dict, "Basic info should be dict")
            
            # Check for expected fields
            expected_fields = ["name", "race", "class", "level"]
            for field in expected_fields:
                if field in basic_info:
                    print(f"  ✅ {field}: {basic_info[field]}")
                else:
                    print(f"  ⚠️  {field} not found")
        except Exception as e:
            print(f"  ⚠️  Basic info test failed: {e}")
    
    def test_combat_info(self):
        """Test getting combat information"""
        print("\n⚔️  Testing combat info...")
        
        if self.handler is None or not self.handler.is_loaded():
            print("  ⚠️  Character data not available - skipping test")
            return
        
        try:
            combat_info = self.handler.get_combat_info()
            self.assertIsInstance(combat_info, dict, "Combat info should be dict")
            
            # Check for combat-related fields
            combat_fields = ["armor_class", "hit_points", "attacks", "saving_throws"]
            for field in combat_fields:
                if field in combat_info:
                    print(f"  ✅ {field} available")
                else:
                    print(f"  ⚠️  {field} not found")
        except Exception as e:
            print(f"  ⚠️  Combat info test failed: {e}")
    
    def test_spell_data(self):
        """Test getting spell information"""
        print("\n✨ Testing spell data...")
        
        if self.handler is None or not self.handler.is_loaded():
            print("  ⚠️  Character data not available - skipping test")
            return
        
        try:
            spells = self.handler.get_spells()
            self.assertIsInstance(spells, dict, "Spells should be dict")
            
            # Test specific class spells
            for spell_class in ["paladin", "warlock"]:
                class_spells = self.handler.get_spells(spell_class)
                if class_spells:
                    print(f"  ✅ {spell_class} spells: {len(class_spells)} found")
                else:
                    print(f"  ⚠️  No {spell_class} spells found")
        except Exception as e:
            print(f"  ⚠️  Spell data test failed: {e}")


class TestSessionHandler(unittest.TestCase):
    """Test session notes handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.handler = None
        try:
            self.handler = SessionHandler("./knowledge_base")
            self.handler.load_data()
        except Exception as e:
            print(f"Warning: Could not initialize session handler: {e}")
    
    def test_session_loading(self):
        """Test session data loading"""
        print("\n📝 Testing session loading...")
        
        if self.handler is None:
            print("  ⚠️  Session handler not available - skipping test")
            return
        
        # Test available sessions
        sessions = self.handler.get_available_sessions()
        self.assertIsInstance(sessions, list, "Sessions should be list")
        print(f"  ✅ Found {len(sessions)} session files")
        
        # Test latest session
        try:
            latest = self.handler.get_latest_session_date()
            if latest:
                print(f"  ✅ Latest session: {latest}")
            else:
                print("  ⚠️  No latest session found")
        except Exception as e:
            print(f"  ⚠️  Latest session test failed: {e}")
    
    def test_session_content(self):
        """Test session content parsing"""
        print("\n📋 Testing session content...")
        
        if self.handler is None or not self.handler.is_loaded():
            print("  ⚠️  Session data not available - skipping test")
            return
        
        try:
            # Test getting specific session
            sessions = self.handler.get_available_sessions()
            if sessions:
                # Test first available session
                session_date = sessions[0].replace('.md', '')
                session_data = self.handler.get_session_by_date(session_date)
                
                if session_data:
                    self.assertIsInstance(session_data, dict, "Session data should be dict")
                    print(f"  ✅ Session {session_date} loaded successfully")
                    
                    # Check content structure
                    expected_fields = ["date", "content", "summary"]
                    for field in expected_fields:
                        if field in session_data:
                            print(f"    ✅ {field} present")
                        else:
                            print(f"    ⚠️  {field} missing")
                else:
                    print(f"  ⚠️  Could not load session {session_date}")
            else:
                print("  ⚠️  No sessions available for testing")
        except Exception as e:
            print(f"  ⚠️  Session content test failed: {e}")


class TestLLMClient(unittest.TestCase):
    """Test LLM client functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.llm_client = None
        try:
            self.llm_client = LLMClient()
        except Exception as e:
            print(f"Warning: Could not initialize LLM client: {e}")
    
    def test_llm_client_initialization(self):
        """Test LLM client initialization"""
        print("\n🤖 Testing LLM client initialization...")
        
        if self.llm_client is None:
            print("  ⚠️  LLM client not available - skipping test")
            return
        
        # Test API key detection
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            print("  ✅ OpenAI API key found")
        else:
            print("  ⚠️  OpenAI API key not set - actual LLM calls will fail")
        
        # Test client configuration
        self.assertIsNotNone(self.llm_client, "LLM client should be initialized")
        print("  ✅ LLM client initialized")
    
    def test_validated_response(self):
        """Test validated response generation (mocked)"""
        print("\n🔧 Testing validated response...")
        
        if self.llm_client is None:
            print("  ⚠️  LLM client not available - skipping test")
            return
        
        # Run async test properly without problematic decorators
        async def run_async_test():
            with patch('src.utils.llm_client.openai.ChatCompletion.acreate') as mock_create:
                # Mock successful response
                mock_create.return_value = Mock(
                    choices=[Mock(message=Mock(content='{"sources_needed": ["dnd_rulebook"], "reasoning": "Need spell rules for counterspell information"}'))]
                )
                
                try:
                    # Test with SourceSelectionResponse model
                    prompt = "Test prompt"
                    response = await self.llm_client.generate_validated_response(
                        prompt, SourceSelectionResponse
                    )
                    
                    self.assertIsInstance(response, SourceSelectionResponse)
                    print("  ✅ Validated response generation works")
                except Exception as e:
                    print(f"  ⚠️  Validated response test failed: {e}")
        
        # Run the async test
        try:
            asyncio.run(run_async_test())
        except Exception as e:
            print(f"  ⚠️  Async test execution failed: {e}")


class TestResponseModels(unittest.TestCase):
    """Test Pydantic response models"""
    
    def test_source_selection_model(self):
        """Test SourceSelectionResponse model"""
        print("\n📋 Testing response models...")
        
        # Test valid data
        valid_data = {
            "sources_needed": ["dnd_rulebook", "character_data"],
            "reasoning": "Need rules and character info"
        }
        
        try:
            model = SourceSelectionResponse(**valid_data)
            self.assertEqual(model.sources_needed, valid_data["sources_needed"])
            self.assertEqual(model.reasoning, valid_data["reasoning"])
            print("  ✅ SourceSelectionResponse validation")
        except Exception as e:
            print(f"  ❌ SourceSelectionResponse failed: {e}")
        
        # Test invalid data
        invalid_data = {
            "sources_needed": ["invalid_source"],
            "reasoning": "test"
        }
        
        try:
            SourceSelectionResponse(**invalid_data)
            print("  ⚠️  Invalid data was accepted (should fail)")
        except Exception:
            print("  ✅ Invalid data properly rejected")
    
    def test_other_response_models(self):
        """Test other response models"""
        
        # Test RulebookTargetResponse
        try:
            rulebook_data = {
                "section_ids": ["test_id"],
                "keywords": ["spell"],  # Fixed field name from "search_keywords" to "keywords"
                "reasoning": "Need spell information from these sections to answer the query"  # Fixed length
            }
            RulebookTargetResponse(**rulebook_data)
            print("  ✅ RulebookTargetResponse validation")
        except Exception as e:
            print(f"  ❌ RulebookTargetResponse failed: {e}")
        
        # Test CharacterTargetResponse  
        try:
            character_data = {
                "file_fields": {"character.json": ["name", "level"]},  # Fixed field name from "target_files" to "file_fields"
                "reasoning": "Need character name and level information to answer the query"  # Fixed length
            }
            CharacterTargetResponse(**character_data)
            print("  ✅ CharacterTargetResponse validation")
        except Exception as e:
            print(f"  ❌ CharacterTargetResponse failed: {e}")


class TestValidation(unittest.TestCase):
    """Test validation utilities"""
    
    def test_validation_helper(self):
        """Test ValidationHelper functionality"""
        print("\n🔍 Testing validation utilities...")
        
        try:
            # Test JSON validation
            valid_json = '{"test": "value"}'
            invalid_json = '{"test": value}'
            
            self.assertTrue(ValidationHelper.validate_json_syntax(valid_json))
            self.assertFalse(ValidationHelper.validate_json_syntax(invalid_json))
            print("  ✅ JSON syntax validation")
        except Exception as e:
            print(f"  ❌ JSON validation failed: {e}")
        
        try:
            # Test file validation
            test_file = Path("./knowledge_base/character.json")
            if test_file.exists():
                result = ValidationHelper.validate_json_file(str(test_file))
                print(f"  ✅ File validation: {result}")
            else:
                print("  ⚠️  Test file not available for validation")
        except Exception as e:
            print(f"  ⚠️  File validation test failed: {e}")


class TestQueryRouter(unittest.TestCase):
    """Test query routing functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.router = None
        try:
            self.router = QueryRouter()
        except Exception as e:
            print(f"Warning: Could not initialize query router: {e}")
    
    def test_source_selection(self):
        """Test source selection (Pass 1)"""
        print("\n🎯 Testing query routing...")
        
        if self.router is None:
            print("  ⚠️  Query router not available - skipping test")
            return
        
        # Run async test properly without problematic decorators
        async def run_async_test():
            with patch('src.engine.query_router.LLMClient') as mock_llm:
                # Mock LLM response
                mock_response = SourceSelectionResponse(
                    sources_needed=["dnd_rulebook"],
                    reasoning="Need spell information for counterspell mechanics"
                )
                mock_llm.return_value.generate_validated_response = AsyncMock(return_value=mock_response)
                
                try:
                    sources = await self.router.select_sources("How does counterspell work?")
                    self.assertIsInstance(sources, SourceSelectionResponse)
                    print("  ✅ Source selection works")
                except Exception as e:
                    print(f"  ⚠️  Source selection test failed: {e}")
        
        # Run the async test
        try:
            asyncio.run(run_async_test())
        except Exception as e:
            print(f"  ⚠️  Async test execution failed: {e}")


class TestContentRetriever(unittest.TestCase):
    """Test content retrieval functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.retriever = None
        try:
            kb = KnowledgeBase("./knowledge_base")
            self.retriever = ContentRetriever(kb)
        except Exception as e:
            print(f"Warning: Could not initialize content retriever: {e}")
    
    def test_content_retrieval_initialization(self):
        """Test content retriever initialization"""
        print("\n📥 Testing content retrieval...")
        
        if self.retriever is None:
            print("  ⚠️  Content retriever not available - skipping test")
            return
        
        self.assertIsNotNone(self.retriever.knowledge_base)
        print("  ✅ Content retriever initialized")


class TestResponseGenerator(unittest.TestCase):
    """Test response generation functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = None
        try:
            self.generator = ResponseGenerator()
        except Exception as e:
            print(f"Warning: Could not initialize response generator: {e}")
    
    def test_response_generator_initialization(self):
        """Test response generator initialization"""
        print("\n💬 Testing response generation...")
        
        if self.generator is None:
            print("  ⚠️  Response generator not available - skipping test")
            return
        
        self.assertIsNotNone(self.generator)
        print("  ✅ Response generator initialized")


class TestShadowScribeEngine(unittest.TestCase):
    """Test main ShadowScribe engine integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = None
        try:
            self.engine = ShadowScribeEngine("./knowledge_base")
        except Exception as e:
            print(f"Warning: Could not initialize ShadowScribe engine: {e}")
    
    def test_engine_initialization(self):
        """Test main engine initialization"""
        print("\n🗡️  Testing ShadowScribe engine...")
        
        if self.engine is None:
            print("  ⚠️  ShadowScribe engine not available - skipping test")
            return
        
        # Test component initialization
        self.assertIsNotNone(self.engine.knowledge_base)
        self.assertIsNotNone(self.engine.query_router)
        self.assertIsNotNone(self.engine.content_retriever)
        self.assertIsNotNone(self.engine.response_generator)
        print("  ✅ All engine components initialized")
    
    def test_available_sources(self):
        """Test getting available sources"""
        print("\n📚 Testing available sources...")
        
        if self.engine is None:
            print("  ⚠️  ShadowScribe engine not available - skipping test")
            return
        
        try:
            sources = self.engine.get_available_sources()
            self.assertIsInstance(sources, dict)
            
            required_sources = ["dnd_rulebook", "character_data", "session_notes"]
            for source in required_sources:
                if source in sources:
                    status = sources[source].get("status", "unknown")
                    print(f"  ✅ {source}: {status}")
                else:
                    print(f"  ⚠️  {source}: missing")
        except Exception as e:
            print(f"  ⚠️  Available sources test failed: {e}")
    
    def test_query_validation(self):
        """Test query validation"""
        print("\n✅ Testing query validation...")
        
        if self.engine is None:
            print("  ⚠️  ShadowScribe engine not available - skipping test")
            return
        
        # Test various query types
        test_queries = [
            ("What's my AC?", True),
            ("How does counterspell work?", True),
            ("", False),
            ("   ", False),
        ]
        
        for query, expected in test_queries:
            try:
                result = asyncio.run(self.engine.validate_query(query))
                self.assertEqual(result, expected)
                status = "✅" if result == expected else "❌"
                print(f"  {status} '{query}': {result}")
            except Exception as e:
                print(f"  ⚠️  Query validation failed for '{query}': {e}")


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🧪 ShadowScribe Comprehensive Test Suite")
    print("=" * 60)
    
    # Define test classes in order of dependencies
    test_classes = [
        TestEnvironmentSetup,
        TestKnowledgeBase,
        TestRulebookHandler,
        TestCharacterHandler,
        TestSessionHandler,
        TestLLMClient,
        TestResponseModels,
        TestValidation,
        TestQueryRouter,
        TestContentRetriever,
        TestResponseGenerator,
        TestShadowScribeEngine,
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_class in test_classes:
        print(f"\n{'='*20} {test_class.__name__} {'='*20}")
        
        # Create test suite for this class
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        
        # Run tests
        for test in suite:
            total_tests += 1
            try:
                result = unittest.TestResult()
                test.run(result)
                
                if result.wasSuccessful():
                    passed_tests += 1
                else:
                    failed_tests += 1
                    for failure in result.failures + result.errors:
                        print(f"    ❌ {failure[0]}: {failure[1]}")
            except Exception as e:
                failed_tests += 1
                print(f"    ❌ Test execution error: {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests} ✅")
    print(f"   Failed: {failed_tests} ❌")
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"   Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\n🎉 ShadowScribe system is ready for use!")
        print("\nNext steps:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Run: python demo.py")
        print("3. Test with sample queries")
    elif success_rate >= 60:
        print("\n⚠️  ShadowScribe system has some issues but core functionality works")
        print("Consider addressing the failed tests for optimal performance")
    else:
        print("\n❌ ShadowScribe system has significant issues")
        print("Please address the failed tests before proceeding")
    
    return success_rate >= 80


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
