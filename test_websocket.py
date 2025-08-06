#!/usr/bin/env python3
"""
Web App Test - Test the actual web app endpoints that the frontend uses
"""

import asyncio
import sys
import os
import websockets
import json

sys.path.insert(0, '/Users/calvinseamons/ShadowScribe')

async def test_websocket_endpoint():
    """Test the WebSocket endpoint that the frontend actually uses."""
    
    print("🌐 Testing Web App WebSocket Endpoint")
    print("=" * 50)
    
    try:
        # Connect to the WebSocket endpoint
        uri = "ws://localhost:8000/ws"
        print(f"🔌 Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Test the same queries that were failing
            test_queries = [
                "Show my spells",
                "Last session summary"
            ]
            
            for i, query in enumerate(test_queries, 1):
                print(f"\n🧪 Test {i}: Sending query '{query}'")
                
                # Send the query
                message = {
                    "query": query
                }
                await websocket.send(json.dumps(message))
                print("📤 Query sent")
                
                # Collect all progress updates and final response
                responses = []
                final_response = None
                
                async for message in websocket:
                    data = json.loads(message)
                    print(f"📥 Received: {data.get('event', 'unknown')} - {data.get('message', '')[:50]}...")
                    
                    responses.append(data)
                    
                    # Check if this is the final response
                    if data.get('event') == 'response_complete':
                        final_response = data.get('data', {}).get('response', '')
                        break
                    elif data.get('event') == 'error':
                        print(f"❌ Error received: {data.get('message')}")
                        break
                
                if final_response:
                    print(f"✅ Query {i} successful!")
                    print(f"📝 Response preview: {final_response[:100]}...")
                    print(f"📊 Progress updates received: {len(responses)}")
                else:
                    print(f"❌ Query {i} failed - no final response received")
    
    except ConnectionRefusedError:
        print("❌ Could not connect to WebSocket - is the web app running?")
        print("💡 To start the web app: npm run dev")
    except Exception as e:
        print(f"❌ WebSocket test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_websocket_endpoint())
