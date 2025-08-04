"""
ShadowScribe LLM Engine Demo - Example usage and testing script.
"""

import asyncio
import os
from src.engine import ShadowScribeEngine
from src.utils import ValidationHelper


async def main():
    """Demonstrate the ShadowScribe LLM Engine functionality."""
    print("🗡️ ShadowScribe LLM Engine Demo")
    print("=" * 50)
    
    # Initialize the engine
    try:
        print("Initializing ShadowScribe Engine...")
        engine = ShadowScribeEngine(knowledge_base_path="./knowledge_base")
        print("✅ Engine initialized successfully!")
        
        # Run system validation
        print("\n🔍 Running system validation...")
        validation_results = ValidationHelper.run_full_system_validation(
            engine.knowledge_base, 
            engine.response_generator.llm_client
        )
        
        print(f"Overall Status: {validation_results['overall_status'].upper()}")
        
        # Display component status
        for component, result in validation_results["components"].items():
            status_emoji = "✅" if result["status"] == "success" else "⚠️" if result["status"] == "warning" else "❌"
            print(f"{status_emoji} {component}: {result['status']}")
        
        # Show warnings if any
        if "warnings" in validation_results:
            print("\n⚠️ Warnings:")
            for warning in validation_results["warnings"]:
                print(f"  - {warning}")
        
        # Demo queries (commented out until LLM client is configured)
        print("\n📚 Knowledge Base Overview:")
        overview = engine.get_available_sources()
        for source, info in overview.items():
            print(f"  {source}: {info['status']} - {info['description']}")
        
        # Example queries to test (will need OpenAI API key)
        sample_queries = [
            "What's my character's AC?",
            "How does counterspell work?", 
            "What happened with Ghul'Vor last session?",
            "Can I cast counterspell to stop that fireball?"
        ]
        
        print(f"\n🎯 Ready to process queries! Example queries:")
        for i, query in enumerate(sample_queries, 1):
            print(f"  {i}. {query}")
        
        # Check for OpenAI API key
        if os.getenv("OPENAI_API_KEY"):
            print(f"\n🤖 Testing sample query...")
            try:
                response = await engine.process_query("What's my character's AC?")
                print(f"Response: {response}")
            except Exception as e:
                print(f"❌ Error processing query: {str(e)}")
        else:
            print(f"\n⚠️ OpenAI API key not found. Set OPENAI_API_KEY to test actual queries.")
            print(f"    Example: set OPENAI_API_KEY=your_key_here")
        
    except Exception as e:
        print(f"❌ Error initializing engine: {str(e)}")
        return
    
    print("\n✨ Demo completed!")


if __name__ == "__main__":
    asyncio.run(main())