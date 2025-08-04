#!/usr/bin/env python3
"""
Interactive ShadowScribe - Main script for terminal-based querying
with comprehensive debug logging to file.
"""

import asyncio
import os
import sys
import traceback
import configparser
from datetime import datetime
from typing import Dict, Any, List

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")
    print("   Or set OPENAI_API_KEY as an environment variable manually.")

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.engine.shadowscribe_engine import ShadowScribeEngine
from src.utils.validation import ValidationHelper


class DebugLogger:
    """Captures and logs all LLM interactions and system outputs."""
    
    def __init__(self, log_file: str = "shadowscribe_debug.txt"):
        self.log_file = log_file
        self.session_start = datetime.now()
        self.clear_log()
    
    def clear_log(self):
        """Clear the debug log file."""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"ShadowScribe Debug Log - Session Started: {self.session_start}\n")
            f.write("=" * 80 + "\n\n")
    
    def log(self, stage: str, content: str, extra_data: Dict[str, Any] = None):
        """Log a debug entry."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {stage}\n")
            f.write("-" * 40 + "\n")
            f.write(f"{content}\n")
            
            if extra_data:
                f.write("\nAdditional Data:\n")
                f.write(f"{json.dumps(extra_data, indent=2, default=str)}\n")
            
            f.write("\n" + "=" * 80 + "\n\n")
    
    def log_error(self, stage: str, error: Exception):
        """Log an error with traceback."""
        self.log(
            f"ERROR - {stage}",
            f"Error Type: {type(error).__name__}\n"
            f"Error Message: {str(error)}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )


class InteractiveShadowScribe:
    """Main interactive interface for ShadowScribe queries."""
    
    def __init__(self):
        self.engine = None
        self.debug_logger = DebugLogger()
        self.session_queries = 0
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from config.ini file."""
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        
        if os.path.exists(config_path):
            config.read(config_path)
            return config
        else:
            # Return default config if file doesn't exist
            print(f"⚠️ Config file not found at {config_path}, using defaults")
            config.add_section('llm')
            config.set('llm', 'model', 'gpt-4o-mini')
            config.set('llm', 'temperature', '0.3')
            config.set('llm', 'max_tokens', '4000')
            return config
    
    def debug_callback(self, stage: str, message: str, data: Dict[str, Any] = None):
        """Callback function for engine debug logging with progress indicators."""
        # Create detailed log entry
        log_data = data if data else {}
        
        # Add timestamp and query ID if available
        if hasattr(self, 'query_id'):
            log_data['query_id'] = self.query_id
        
        # Log to file with full details
        self.debug_logger.log(stage, message, log_data)
        
        # Show progress indicators in terminal
        if stage == "PASS_1_START":
            print("  🔍 Pass 1: Selecting knowledge sources...")
        elif stage == "PASS_1_COMPLETE":
            sources = data.get('selected_sources', []) if data else []
            print(f"  ✅ Pass 1: Selected {len(sources)} source(s)")
            if data and 'reasoning' in data:
                print(f"    Reasoning: {data['reasoning'][:100]}...")
        elif stage == "PASS_2_START":
            print("  🎯 Pass 2: Targeting specific content...")
        elif stage == "PASS_2_COMPLETE":
            print("  ✅ Pass 2: Content targets identified")
        elif stage == "PASS_3_START":
            print("  📚 Pass 3: Retrieving relevant information...")
        elif stage == "PASS_3_COMPLETE":
            content_summary = data.get('content_summary', {}) if data else {}
            print(f"  ✅ Pass 3: Retrieved {len(content_summary)} content section(s)")
        elif stage == "PASS_4_START":
            print("  🧠 Pass 4: Generating response...")
        elif stage == "PASS_4_COMPLETE":
            response_length = data.get('response_length', 0) if data else 0
            print(f"  ✅ Pass 4: Generated {response_length} character response")
        elif stage == "ERROR":
            print(f"  ❌ Error in {message}")
    
    async def initialize(self):
        """Initialize the ShadowScribe engine with validation."""
        print("🌙 Initializing ShadowScribe Engine...")
        self.debug_logger.log("INITIALIZATION", "Starting ShadowScribe engine initialization")
        
        try:
            # Load configuration to get model settings
            config = configparser.ConfigParser()
            config_file = os.path.join(os.path.dirname(__file__), 'config.ini')
            
            if os.path.exists(config_file):
                config.read(config_file)
                model = config.get('llm', 'model', fallback='gpt-4o-mini')
                print(f"🤖 Using AI Model: {model}")
            else:
                model = 'gpt-4o-mini'
                print(f"🤖 Using AI Model: {model} (default - no config.ini found)")
            
            # Initialize engine with configured model
            self.engine = ShadowScribeEngine(
                knowledge_base_path="./knowledge_base",
                model=model
            )
            
            # Set up debug callback
            self.engine.set_debug_callback(self.debug_callback)
            
            self.debug_logger.log("ENGINE_INIT", "ShadowScribe engine created successfully")
            
            # Run system validation
            print("🔍 Running system validation...")
            await self.run_validation()
            
            # Show available sources
            self.show_available_sources()
            
            print("✅ ShadowScribe is ready!")
            print(f"📝 Debug output will be saved to: {self.debug_logger.log_file}")
            
        except Exception as e:
            self.debug_logger.log_error("INITIALIZATION", e)
            print(f"❌ Failed to initialize ShadowScribe: {str(e)}")
            raise
    
    async def run_validation(self):
        """Run comprehensive system validation."""
        try:
            # Validate knowledge base
            knowledge_base = self.engine.knowledge_base
            
            # Check character data
            if hasattr(knowledge_base, 'character'):
                character_validation = ValidationHelper.validate_character_data(knowledge_base.character)
                self.debug_logger.log("VALIDATION - Character Data", 
                                    "Character data validation completed", 
                                    character_validation)
                
                if character_validation.get("status") == "success":
                    print("  ✅ Character data loaded successfully")
                else:
                    print("  ⚠️ Character data has issues")
            
            # Check rulebook data
            if hasattr(knowledge_base, 'rulebook'):
                rulebook_validation = ValidationHelper.validate_rulebook_data(knowledge_base.rulebook)
                self.debug_logger.log("VALIDATION - Rulebook Data", 
                                    "Rulebook data validation completed", 
                                    rulebook_validation)
                
                if rulebook_validation.get("status") == "success":
                    print("  ✅ D&D rulebook data loaded successfully")
                else:
                    print("  ⚠️ Rulebook data has issues")
            
            # Check session data
            if hasattr(knowledge_base, 'sessions'):
                session_validation = ValidationHelper.validate_session_data(knowledge_base.sessions)
                self.debug_logger.log("VALIDATION - Session Data", 
                                    "Session data validation completed", 
                                    session_validation)
                
                if session_validation.get("status") == "success":
                    print("  ✅ Session notes loaded successfully")
                else:
                    print("  ⚠️ Session data has issues")
                    
        except Exception as e:
            self.debug_logger.log_error("VALIDATION", e)
            print(f"  ⚠️ Validation encountered errors: {str(e)}")
    
    def show_available_sources(self):
        """Display available knowledge sources."""
        try:
            sources = self.engine.get_available_sources()
            self.debug_logger.log("AVAILABLE_SOURCES", "Retrieved available sources", sources)
            
            print("\n📚 Available Knowledge Sources:")
            for source_type, details in sources.items():
                if isinstance(details, dict):
                    count = details.get('count', 'Unknown')
                    print(f"  • {source_type}: {count} items")
                else:
                    print(f"  • {source_type}: Available")
            
        except Exception as e:
            self.debug_logger.log_error("AVAILABLE_SOURCES", e)
            print(f"⚠️ Could not retrieve source information: {str(e)}")
    
    async def process_query_with_debug(self, user_query: str) -> str:
        """Process a query with comprehensive debug logging."""
        self.session_queries += 1
        query_id = f"Query_{self.session_queries}"
        
        self.debug_logger.log(f"{query_id} - USER_INPUT", f"User Query: {user_query}")
        
        try:
            print(f"🤔 Processing query: {user_query}")
            print("⏳ Running 4-pass analysis...")
            
            # Track progress
            self.current_pass = 0
            self.query_id = query_id
            
            # Process the query
            response = await self.engine.process_query(user_query)
            
            print("✅ Analysis complete!")
            
            self.debug_logger.log(f"{query_id} - FINAL_RESPONSE", f"Generated Response: {response}")
            
            return response
            
        except Exception as e:
            self.debug_logger.log_error(f"{query_id} - PROCESSING", e)
            error_response = f"❌ Error processing query: {str(e)}"
            return error_response
    
    async def run_interactive_session(self):
        """Run the main interactive query session."""
        print("\n" + "="*60)
        print("🌙 ShadowScribe Interactive Session")
        print("="*60)
        print("Ask questions about Duskryn Nightwarden, D&D rules, or session events.")
        print("Type 'quit', 'exit', or 'q' to end the session.")
        print("Type 'help' for example queries.")
        print("Type 'sources' to see available knowledge sources.")
        print("="*60 + "\n")
        
        while True:
            try:
                # Get user input
                user_input = input("🎲 Your Query: ").strip()
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Farewell, adventurer!")
                    break
                
                if user_input.lower() == 'help':
                    self.show_example_queries()
                    continue
                
                if user_input.lower() == 'sources':
                    self.show_available_sources()
                    continue
                
                if not user_input:
                    print("⚠️ Please enter a query or 'quit' to exit.")
                    continue
                
                # Process the query
                print()  # Add spacing
                response = await self.process_query_with_debug(user_input)
                
                # Display response
                print(f"\n📜 ShadowScribe Response:")
                print("-" * 40)
                print(response)
                print("-" * 40 + "\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                self.debug_logger.log_error("INTERACTIVE_SESSION", e)
                print(f"\n❌ Unexpected error: {str(e)}")
                print("Please try again or type 'quit' to exit.\n")
    
    def show_example_queries(self):
        """Display example queries for users."""
        examples = [
            "What's my character's AC?",
            "How does counterspell work?",
            "What spells do I have available?",
            "Tell me about my covenant with Ghul'Vor",
            "What happened with Ghul'Vor in the last session?",
            "Can I counterspell that fireball with my warlock slots?",
            "What magical items does Duskryn have?",
            "What are my character's goals and objectives?",
            "How much HP do I have?",
            "What are my spell save DCs?"
        ]
        
        print("\n💡 Example Queries:")
        for i, example in enumerate(examples, 1):
            print(f"  {i}. {example}")
        print()


async def main():
    """Main entry point for the interactive ShadowScribe session."""
    print("🌙 Welcome to ShadowScribe - Your D&D Intelligence Assistant")
    print("="*60)
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found.")
        print("\n💡 You can set your API key in one of these ways:")
        print("   1. Create a .env file in this directory with:")
        print("      OPENAI_API_KEY=your-api-key-here")
        print("   2. Set it as an environment variable:")
        print("      export OPENAI_API_KEY='your-api-key-here'")
        print("   3. Set it in your shell profile (~/.bashrc, ~/.zshrc, etc.)")
        
        # Check if .env file exists but doesn't have the key
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_file):
            print(f"\n📄 Found .env file at: {env_file}")
            print("   Make sure it contains: OPENAI_API_KEY=your-api-key-here")
        else:
            print(f"\n📄 No .env file found. You can create one at: {env_file}")
        
        return
    
    try:
        # Initialize and run interactive session
        shadowscribe = InteractiveShadowScribe()
        await shadowscribe.initialize()
        await shadowscribe.run_interactive_session()
        
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        print("Check the debug log for detailed error information.")


if __name__ == "__main__":
    # Import json for debug logger
    import json
    
    # Run the interactive session
    asyncio.run(main())
