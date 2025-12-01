"""
Interactive Central Engine Demo

Simple script that lets you ask questions to the CentralEngine and see:
- Router decisions (which routers are needed)
- Performance metrics
- Full response from the model
- All using config.py settings

Also stores routing feedback to the database for training data collection.
"""
import asyncio
import sys
from pathlib import Path
import json
import argparse
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.central_engine import CentralEngine
from src.llm.central_prompt_manager import CentralPromptManager
from src.rag.context_assembler import ContextAssembler
from src.config import get_config
from src.rag.character.character_manager import CharacterManager
from src.rag.rulebook.rulebook_storage import RulebookStorage
from src.rag.session_notes.session_notes_storage import SessionNotesStorage

# Database imports for feedback storage
from api.database.connection import AsyncSessionLocal
from api.database.feedback_models import RoutingFeedback
from api.database.repositories.feedback_repo import FeedbackRepository


class InteractiveCentralEngineDemo:
    """Interactive demo that shows routing decisions and performance"""
    
    def __init__(self, verbose: bool = True, routing_mode: str = "llm"):
        """Initialize the demo with CentralEngine
        
        Args:
            verbose: Whether to show detailed initialization output
            routing_mode: "llm" (default), "local", or "compare"
        """
        self.verbose = verbose
        self.routing_mode = routing_mode
        
        if verbose:
            print("🚀 Initializing ShadowScribe2.0 Central Engine...")
            if routing_mode == "local":
                print("   🧠 Using LOCAL MODEL for routing (no LLM router calls)")
            elif routing_mode == "compare":
                print("   🔬 Using COMPARE mode (LLM routing + local comparison)")
            else:
                print("   ☁️  Using LLM for routing")
        
        # Load config
        self.config = get_config()
        if verbose:
            print(f"   Config loaded - Router: {self.config.router_llm_provider}, Final: {self.config.final_response_llm_provider}")
        
        # Load storage components
        if verbose:
            print("📦 Loading storage components...")
        
        # Load Duskryn character
        character_manager = CharacterManager()
        character_name = "Duskryn Nightwarden"
        try:
            character = character_manager.load_character(character_name)
            if verbose:
                print(f"   ✅ Character loaded: {character.character_base.name}")
            self.character_name = character.character_base.name
        except Exception as e:
            if verbose:
                print(f"   ⚠️  Failed to load character: {e}")
            character = None
            self.character_name = "Demo Character"
        
        # Load rulebook storage
        try:
            rulebook_storage = RulebookStorage()
            if rulebook_storage.load_from_disk("rulebook_storage.pkl"):
                if verbose:
                    print(f"   ✅ Rulebook storage loaded")
            else:
                if verbose:
                    print(f"   ⚠️  Rulebook storage file not found")
                rulebook_storage = None
        except Exception as e:
            if verbose:
                print(f"   ⚠️  Failed to load rulebook storage: {e}")
            rulebook_storage = None
        
        # Load session notes storage
        try:
            session_notes_storage = SessionNotesStorage()
            main_campaign = session_notes_storage.get_campaign("main_campaign")
            if main_campaign:
                if verbose:
                    print(f"   ✅ Session notes storage loaded for main_campaign")
            else:
                if verbose:
                    print(f"   ⚠️  Main campaign not found in session notes")
                main_campaign = None
        except Exception as e:
            if verbose:
                print(f"   ⚠️  Failed to load session notes: {e}")
            main_campaign = None
        
        # Create components
        self.context_assembler = ContextAssembler()
        self.prompt_manager = CentralPromptManager(self.context_assembler)
        
        # Configure comparison logging based on routing mode
        if routing_mode == "compare":
            self.config.comparison_logging = True
        else:
            # For local or llm mode, disable comparison
            self.config.comparison_logging = False
        
        # Override use_local_classifier based on routing mode
        if routing_mode == "local":
            self.config.use_local_classifier = True
        elif routing_mode == "llm":
            self.config.use_local_classifier = False
        # "compare" mode keeps whatever is in config
        
        # Create central engine using config with storage components
        self.engine = CentralEngine.create_from_config(
            self.prompt_manager,
            character=character,
            rulebook_storage=rulebook_storage,
            campaign_session_notes=main_campaign
        )
        
        # Store references for local routing
        self.character = character
        self.campaign_session_notes = main_campaign
        
        if verbose:
            print(f"   LLM Clients available: {list(self.engine.llm_clients.keys())}")
            print("✅ Central Engine ready!\n")
    
    async def process_query_with_visibility(self, user_query: str, character_name: str = None, show_details: bool = True):
        """Process a query with full visibility into routing and performance
        
        Args:
            user_query: The user's question
            character_name: Character name to use (defaults to loaded character)
            show_details: Whether to show detailed processing information
        """
        
        # Use loaded character name if none provided
        if character_name is None:
            character_name = self.character_name
        
        if show_details:
            print("=" * 80)
            print(f"🎯 PROCESSING QUERY: '{user_query}'")
            print(f"📋 Character: {character_name}")
            print("=" * 80)
        
        import time
        start_time = time.time()
        
        # Track routing info for feedback storage
        routing_info: Dict[str, Any] = {
            'tools_needed': None,
            'entities': None,
            'normalized_query': None,
            'backend': 'local' if self.routing_mode == 'local' else 'llm',
            'inference_time_ms': None
        }
        
        async def capture_metadata(event_type: str, data: dict):
            """Callback to capture routing metadata for feedback storage."""
            if event_type == 'routing_metadata':
                routing_info['tools_needed'] = data.get('tools_needed', [])
                routing_info['backend'] = data.get('classifier_backend', 'local')
                routing_info['normalized_query'] = data.get('normalized_query')
                routing_info['entities'] = data.get('extracted_entities', [])
                routing_info['inference_time_ms'] = data.get('local_inference_time_ms')
        
        # Stream the response from CentralEngine
        final_response = ""
        try:
            if show_details:
                print(f"\n🎯 FINAL RESPONSE (streaming)")
                print("=" * 80)
            else:
                print(f"\n💬 Response:")
            
            async for chunk in self.engine.process_query_stream(
                user_query, 
                character_name,
                metadata_callback=capture_metadata
            ):
                print(chunk, end='', flush=True)
                final_response += chunk
            
            print()  # New line after streaming completes
            
            # Store routing feedback to database
            await self._store_routing_feedback(routing_info, character_name, show_details)
            
        except Exception as e:
            print(f"\n❌ Error processing query: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}"
        
        execution_time = time.time() - start_time
        
        if show_details:
            print(f"\n🏃 Total execution time: {execution_time:.2f}s")
            print(f"📏 Response length: {len(final_response)} characters")
            
            # Show configuration used
            print(f"\n⚙️  CONFIGURATION USED")
            print("-" * 40)
            print(f"Router Model: {self.config.anthropic_router_model if self.config.router_llm_provider == 'anthropic' else self.config.openai_router_model}")
            print(f"Router Temp: {self.config.router_temperature}")
            print(f"Router Max Tokens: {self.config.router_max_tokens}")
            print(f"Final Model: {self.config.anthropic_final_model if self.config.final_response_llm_provider == 'anthropic' else self.config.openai_final_model}")
            print(f"Final Temp: {self.config.final_temperature}")
            print(f"Final Max Tokens: {self.config.final_max_tokens}")
            print("=" * 80)
        
        return final_response
    
    async def _store_routing_feedback(self, routing_info: Dict[str, Any], character_name: str, show_details: bool):
        """Store routing feedback to the database for training data collection.
        
        Args:
            routing_info: Dictionary containing tools_needed, entities, normalized_query, etc.
            character_name: Name of the character used
            show_details: Whether to show feedback storage confirmation
        """
        if not routing_info['tools_needed'] or not routing_info['normalized_query']:
            if show_details:
                print("⚠️  No routing info to store (missing tools or query)")
            return
        
        try:
            async with AsyncSessionLocal() as db:
                repo = FeedbackRepository(db)
                
                # Convert entities to serializable format
                entities_data = None
                if routing_info['entities']:
                    entities_data = [
                        {
                            'name': e.get('name', ''),
                            'text': e.get('text', ''),
                            'type': e.get('type', ''),
                            'confidence': e.get('confidence', 1.0)
                        }
                        for e in routing_info['entities']
                    ]
                
                # Create feedback record
                feedback_record = RoutingFeedback(
                    user_query=routing_info['normalized_query'],
                    character_name=character_name,
                    campaign_id='main_campaign',
                    predicted_tools=routing_info['tools_needed'],
                    predicted_entities=entities_data,
                    classifier_backend=routing_info['backend'],
                    classifier_inference_time_ms=routing_info['inference_time_ms']
                )
                
                created = await repo.create(feedback_record)
                await db.commit()
                
                if show_details:
                    print(f"💾 Routing feedback stored (ID: {created.id[:8]}...)")
                    
        except Exception as e:
            if show_details:
                print(f"⚠️  Failed to store routing feedback: {e}")
    
    async def _debug_tool_selector_response(self, user_query: str):
        """Debug the tool selector LLM response to see what's working"""
        print("\n🔍 DEBUGGING TOOL SELECTOR RESPONSE")
        print("-" * 50)
        
        try:
            # Use the actual prompt method from CentralPromptManager
            tool_selector_prompt = self.prompt_manager.get_tool_and_intention_selector_prompt(user_query, self.character_name)
            
            # Get the same client the engine would use
            provider = self.config.router_llm_provider
            client = self.engine.llm_clients.get(provider)
            
            if provider == "anthropic":
                model = self.config.anthropic_router_model
            else:
                model = self.config.openai_router_model
                
            llm_params = self.config.get_router_llm_params(model)
            
            print(f"Provider: {provider}, Model: {model}")
            print(f"LLM Params: {llm_params}")
            print("\n📝 FULL PROMPT:")
            print("-" * 80)
            print(tool_selector_prompt)
            print("-" * 80)
            
            # Make the raw call
            response = await client.generate_json_response(tool_selector_prompt, model=model, **llm_params)
            print("\n📤 RAW LLM RESPONSE (before any JSON repair):")
            print(json.dumps(response, indent=2))
            
        except Exception as e:
            print(f"Debug error: {e}")
            import traceback
            traceback.print_exc()
    
    async def _debug_entity_extractor_response(self, user_query: str):
        """Debug the entity extractor LLM response to see what's working"""
        print("\n🔍 DEBUGGING ENTITY EXTRACTOR RESPONSE")
        print("-" * 50)
        
        try:
            # Use the actual prompt method from CentralPromptManager
            entity_prompt = self.prompt_manager.get_entity_extractor_prompt(user_query)
            
            # Get the same client the engine would use
            provider = self.config.router_llm_provider
            client = self.engine.llm_clients.get(provider)
            
            if provider == "anthropic":
                model = self.config.anthropic_router_model
            else:
                model = self.config.openai_router_model
                
            llm_params = self.config.get_router_llm_params(model)
            
            print(f"Provider: {provider}, Model: {model}")
            print(f"LLM Params: {llm_params}")
            print("\nPrompt:")
            print("-" * 30)
            print(entity_prompt[:500] + "..." if len(entity_prompt) > 500 else entity_prompt)
            print("-" * 30)
            
            # Make the raw call
            response = await client.generate_json_response(entity_prompt, model=model, **llm_params)
            print("\nRAW RESPONSE:")
            print(json.dumps(response, indent=2))
            
        except Exception as e:
            print(f"Debug error: {e}")
            import traceback
            traceback.print_exc()
    
    
    
    async def process_single_query(self, query: str, show_details: bool = False):
        """Process a single query and return the response
        
        Args:
            query: The question to process
            show_details: Whether to show detailed processing information
            
        Returns:
            The response string
        """
        return await self.process_query_with_visibility(query, show_details=show_details)
    
    def run_interactive_demo(self):
        """Run the interactive demo loop"""
        print("🎮 Interactive ShadowScribe2.0 Demo")
        print("Type your questions below. Type 'quit' to exit.\n")
        
        while True:
            try:
                # Get user input
                user_query = input("❓ Your question: ").strip()
                
                if user_query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Thanks for using ShadowScribe2.0!")
                    break
                
                if not user_query:
                    print("Please enter a question.\n")
                    continue
                
                # Process the query
                try:
                    asyncio.run(self.process_query_with_visibility(user_query))
                except Exception as e:
                    print(f"❌ Error processing query: {str(e)}")
                    print("\n🔍 Running debug to show raw LLM responses...")
                    # Debug raw LLM responses
                    try:
                        asyncio.run(self._debug_tool_selector_response(user_query))
                    except Exception as debug_e:
                        print(f"Tool selector debug failed: {debug_e}")
                    try:
                        asyncio.run(self._debug_entity_extractor_response(user_query))
                    except Exception as debug_e:
                        print(f"Entity extractor debug failed: {debug_e}")
                
                print("\n" + "="*80 + "\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Thanks for using ShadowScribe2.0!")
                break
            except Exception as e:
                print(f"❌ Error processing query: {str(e)}")
                print("Please try again.\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="ShadowScribe2.0 Central Engine Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ask a single question (default: compare LLM vs local routing)
  python demo_central_engine.py -q "What is Duskryn's alignment?"
  
  # Use LOCAL model for routing (faster, no LLM router calls)
  python demo_central_engine.py -q "What is my AC?" --routing local
  
  # Use LLM only for routing (no local comparison)
  python demo_central_engine.py -q "What is my AC?" --routing llm
  
  # Compare LLM and local routing (default)
  python demo_central_engine.py -q "What is my AC?" --routing compare
  
  # Ask multiple questions in sequence (maintains context)
  python demo_central_engine.py -q "What is my AC?" -q "What about my HP?"
  
  # Run in interactive mode
  python demo_central_engine.py
  
  # Run quietly with minimal output
  python demo_central_engine.py -q "What spells can I cast?" --quiet --routing local
        """
    )
    parser.add_argument(
        "-q", "--query",
        action="append",
        help="Query to process. Can be used multiple times for sequential questions."
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output - just show responses without details"
    )
    parser.add_argument(
        "--routing",
        choices=["llm", "local", "compare"],
        default="compare",
        help="Routing mode: 'llm' (LLM only), 'local' (local model only), 'compare' (LLM + local comparison, default)"
    )
    parser.add_argument(
        "--no-test",
        action="store_true",
        help="Skip the auto-test query on startup"
    )
    
    args = parser.parse_args()
    try:
        # Initialize demo with appropriate verbosity and routing mode
        demo = InteractiveCentralEngineDemo(
            verbose=not args.quiet,
            routing_mode=args.routing
        )
        
        # Handle command-line queries
        if args.query:
            # Process queries from command line
            for i, query in enumerate(args.query):
                if i > 0 and not args.quiet:
                    print("\n" + "="*80 + "\n")
                    print(f"📝 Conversation question {i+1}/{len(args.query)}")
                
                try:
                    response = asyncio.run(demo.process_single_query(
                        query, 
                        show_details=not args.quiet
                    ))
                except Exception as e:
                    print(f"❌ Error processing query: {str(e)}")
                    if not args.quiet:
                        import traceback
                        traceback.print_exc()
            
            # Show conversation summary if multiple queries
            if len(args.query) > 1 and not args.quiet:
                print("\n" + "="*80)
                print("📚 Conversation Summary")
                print("="*80)
                print(f"Total queries: {len(args.query)}")
                history = demo.engine.get_conversation_history()
                print(f"Conversation length: {len(history)} turns")
        
        else:
            # Interactive mode
            demo.run_interactive_demo()
    except Exception as e:
        print(f"❌ Failed to initialize demo: {str(e)}")
        print("Make sure you have activated the virtual environment and set up your API keys.")


if __name__ == "__main__":
    main()
