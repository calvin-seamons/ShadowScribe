#!/usr/bin/env python3
"""
End-to-End System Test - Tests the complete ShadowScribe pipeline from frontend entry point
"""

import asyncio
import sys
import os
import traceback

sys.path.insert(0, '/Users/calvinseamons/ShadowScribe')

from src.engine.shadowscribe_engine import ShadowScribeEngine

async def test_full_pipeline():
    """Test the complete system pipeline like the frontend would use it."""
    
    print("🔍 End-to-End ShadowScribe System Test")
    print("=" * 60)
    print("Testing the complete pipeline that the frontend uses...")
    print("")
    
    # Debug callback to capture what's happening
    debug_logs = []
    
    def debug_callback(event_type, message, data=None):
        debug_logs.append({
            "event": event_type,
            "message": message,
            "data": data or {}
        })
        print(f"📊 {event_type}: {message}")
        if data:
            print(f"   📋 Data: {str(data)[:100]}...")
    
    try:
        # Initialize the engine like the web app does
        print("⚙️  Initializing ShadowScribe Engine...")
        engine = ShadowScribeEngine(
            knowledge_base_path="/Users/calvinseamons/ShadowScribe/knowledge_base",
            model="gpt-4.1-mini"
        )
        
        # Set the debug callback
        engine.set_debug_callback(debug_callback)
        print("✅ Engine initialized successfully")
        print("")
        
        # Test queries that are failing in the frontend
        test_queries = [
            "Show my spells",
            "Last session summary"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"🧪 Test {i}: Processing query '{query}'")
            print("-" * 40)
            
            try:
                # This is the exact same call the frontend makes
                response = await engine.process_query(query)
                
                print(f"✅ Query processed successfully!")
                print(f"📝 Response: {response[:200]}...")
                print(f"📊 Debug events captured: {len(debug_logs)}")
                
            except Exception as e:
                print(f"❌ Query failed with error: {str(e)}")
                print(f"🔍 Error type: {type(e).__name__}")
                traceback.print_exc()
                
                # Show recent debug logs
                print(f"📊 Recent debug events:")
                for log in debug_logs[-5:]:
                    print(f"   - {log['event']}: {log['message']}")
            
            # Clear debug logs for next test
            debug_logs.clear()
            print("")
    
    except Exception as e:
        print(f"💥 System initialization failed: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
