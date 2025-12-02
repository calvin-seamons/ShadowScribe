"""WebSocket router for real-time chat and character creation."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import json
import uuid
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path for character builder imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from api.database.connection import get_db, AsyncSessionLocal
from api.services.chat_service import ChatService
from api.services.dndbeyond_service import DndBeyondService
from api.database.feedback_models import RoutingFeedback
from api.database.repositories.feedback_repo import FeedbackRepository
from src.character_creation.async_character_builder import AsyncCharacterBuilder

router = APIRouter()

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat.
    
    Uses local model for routing and Gazetteer NER for entity extraction.
    Entity extraction depends on the selected character and campaign.
    
    Message Types (Client -> Server):
        - message: Send a chat message
          {
            "type": "message",
            "message": "What is my AC?",
            "character_name": "Duskryn Nightwarden",
            "campaign_id": "main_campaign"  // optional, defaults to "main_campaign"
          }
        - clear_history: Clear conversation history
          {
            "type": "clear_history",
            "character_name": "Duskryn Nightwarden",
            "campaign_id": "main_campaign"  // optional
          }
        - ping: Keep-alive ping
    
    Message Types (Server -> Client):
        - message_received: Acknowledgment that message was received
        - response_chunk: Streamed response chunk
        - response_complete: Response streaming finished
        - error: Error occurred
        - history_cleared: Conversation history cleared
        - routing_metadata: Which tools were selected
        - entities_metadata: Entities extracted from query
        - context_sources: Sources used for response
        - performance_metrics: Timing information
        - pong: Keep-alive response
    """
    await websocket.accept()
    
    connection_id = str(uuid.uuid4())
    active_connections[connection_id] = websocket
    
    # Initialize chat service - routing mode determined by config
    chat_service = ChatService()
    
    # Track current query's routing info for feedback collection
    current_routing_info = {
        'tools_needed': None,
        'entities': None,
        'normalized_query': None,  # Placeholder-ized query from CentralEngine
        'backend': 'local',
        'inference_time_ms': None
    }
    
    async def emit_metadata(event_type: str, data: dict):
        """Callback to emit metadata events to the client and capture for feedback."""
        # Capture routing info for feedback collection
        if event_type == 'routing_metadata':
            current_routing_info['tools_needed'] = data.get('tools_needed', [])
            current_routing_info['backend'] = data.get('classifier_backend', 'local')
            # Capture normalized query (placeholder-ized) from CentralEngine
            current_routing_info['normalized_query'] = data.get('normalized_query')
            # Capture extracted entities with text/type for training data
            current_routing_info['entities'] = data.get('extracted_entities', [])
            # Capture local classifier timing if available (comparison mode)
            current_routing_info['inference_time_ms'] = data.get('local_inference_time_ms')
        
        await websocket.send_json({
            'type': event_type,
            'data': data
        })
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Extract message details
            message_type = message_data.get('type')
            
            if message_type == 'ping':
                await websocket.send_json({'type': 'pong'})
                continue
            
            if message_type == 'clear_history':
                character_name = message_data.get('character_name')
                campaign_id = message_data.get('campaign_id', 'main_campaign')
                if character_name:
                    chat_service.clear_conversation_history(character_name, campaign_id)
                    await websocket.send_json({'type': 'history_cleared'})
                continue
            
            user_message = message_data.get('message')
            character_name = message_data.get('character_name')
            campaign_id = message_data.get('campaign_id', 'main_campaign')
            
            # Validate input
            if not user_message or not character_name:
                await websocket.send_json({
                    'type': 'error',
                    'error': 'Missing required fields: message, character_name'
                })
                continue
            
            # Send acknowledgment
            await websocket.send_json({'type': 'message_received'})
            
            # Reset routing info for this query
            current_routing_info['tools_needed'] = None
            current_routing_info['entities'] = None
            current_routing_info['normalized_query'] = None
            current_routing_info['inference_time_ms'] = None
            
            # Stream response from CentralEngine
            try:
                async for chunk in chat_service.process_query_stream(
                    user_message, 
                    character_name,
                    campaign_id=campaign_id,
                    metadata_callback=emit_metadata
                ):
                    await websocket.send_json({
                        'type': 'response_chunk',
                        'content': chunk
                    })
                
                # Send completion signal
                await websocket.send_json({'type': 'response_complete'})
                
                # Record routing decision for feedback collection
                if current_routing_info['tools_needed'] and current_routing_info['normalized_query']:
                    try:
                        async with AsyncSessionLocal() as db:
                            repo = FeedbackRepository(db)

                            # Convert entities to serializable format
                            entities_data = None
                            if current_routing_info['entities']:
                                entities_data = [
                                    {
                                        'name': e.get('name', ''),
                                        'text': e.get('text', ''),
                                        'type': e.get('type', ''),
                                        'confidence': e.get('confidence', 1.0)
                                    }
                                    for e in current_routing_info['entities']
                                ]

                            # Use normalized query from CentralEngine (already has placeholders applied)
                            feedback_record = RoutingFeedback(
                                user_query=current_routing_info['normalized_query'],
                                character_name=character_name,
                                campaign_id=campaign_id,
                                predicted_tools=current_routing_info['tools_needed'],
                                predicted_entities=entities_data,
                                classifier_backend=current_routing_info['backend'],
                                classifier_inference_time_ms=current_routing_info['inference_time_ms']
                            )

                            created = await repo.create(feedback_record)
                            await db.commit()

                            # Send feedback ID to client for later feedback submission
                            await websocket.send_json({
                                'type': 'feedback_id',
                                'data': {'id': created.id}
                            })
                    except Exception as e:
                        print(f"Failed to record routing feedback: {e}")
                
            except Exception as e:
                await websocket.send_json({
                    'type': 'error',
                    'error': f'Error processing query: {str(e)}'
                })
    
    except WebSocketDisconnect:
        print(f"Client disconnected: {connection_id}")
    except Exception as e:
        print(f"Error in WebSocket connection: {str(e)}")
        try:
            await websocket.send_json({
                'type': 'error',
                'error': str(e)
            })
        except:
            pass
    finally:
        # Clean up connection
        if connection_id in active_connections:
            del active_connections[connection_id]
        try:
            await websocket.close()
        except:
            pass


@router.websocket("/ws/character/create")
async def character_creation_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for character creation with real-time progress updates.
    
    Message Types (Client -> Server):
        - create_character: Start character creation
          {
            "type": "create_character",
            "url": "https://dndbeyond.com/characters/152248393"
          }
        - ping: Keep-alive ping
    
    Message Types (Server -> Client):
        - parser_started: Parser has begun execution
        - parser_complete: Parser has finished
        - parser_error: Parser encountered an error
        - assembly_started: Character object assembly begun
        - creation_complete: Character creation finished
        - creation_error: Character creation failed
        - pong: Keep-alive response
    """
    await websocket.accept()
    
    connection_id = str(uuid.uuid4())
    active_connections[connection_id] = websocket
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get('type')
            
            # Handle ping
            if message_type == 'ping':
                await websocket.send_json({'type': 'pong'})
                continue
            
            # Handle character creation
            if message_type == 'create_character':
                url = message_data.get('url')
                json_data = message_data.get('json_data')
                
                # Validate input - need either URL or json_data
                if not url and not json_data:
                    await websocket.send_json({
                        'type': 'creation_error',
                        'error': 'Missing required field: url or json_data'
                    })
                    continue
                
                try:
                    # Step 1: Fetch character JSON if URL provided
                    if url:
                        # Extract character ID
                        character_id = DndBeyondService.extract_character_id(url)
                        if not character_id:
                            await websocket.send_json({
                                'type': 'creation_error',
                                'error': 'Invalid D&D Beyond URL format'
                            })
                            continue
                        
                        # Emit fetch started event
                        await websocket.send_json({
                            'type': 'fetch_started',
                            'character_id': character_id
                        })
                        
                        # Fetch character data
                        json_data = await DndBeyondService.fetch_character_json(character_id)
                        
                        # Emit fetch complete event
                        await websocket.send_json({
                            'type': 'fetch_complete',
                            'character_id': character_id,
                            'character_name': json_data.get('data', {}).get('name', 'Unknown')
                        })
                    
                    # Step 2: Parse character with async builder
                    async def progress_callback(event):
                        """Forward progress events to WebSocket client."""
                        # Don't forward the builder's creation_complete event
                        # as we'll send our own with the full character data
                        if event['type'] != 'creation_complete':
                            await websocket.send_json(event)
                    
                    builder = AsyncCharacterBuilder(json_data)
                    character = await builder.build_async(progress_callback=progress_callback)
                    
                    # Step 3: Serialize character for response
                    from dataclasses import asdict
                    from datetime import datetime
                    import json as json_lib
                    
                    def serialize_datetime(obj):
                        """Custom JSON encoder for datetime objects."""
                        if isinstance(obj, datetime):
                            return obj.isoformat()
                        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
                    
                    character_dict = asdict(character)
                    
                    # Pre-serialize character_data to handle datetime objects
                    character_data_json = json_lib.loads(
                        json_lib.dumps(character_dict, default=serialize_datetime)
                    )
                    
                    # Send full parsed character data for frontend editing
                    await websocket.send_json({
                        'type': 'creation_complete',
                        'character_id': character.character_base.name,
                        'character_name': character.character_base.name,
                        'character_data': character_data_json,
                        'character_summary': {
                            'name': character.character_base.name,
                            'race': character.character_base.race,
                            'character_class': character.character_base.character_class,
                            'level': character.character_base.total_level,
                            'hp': character.combat_stats.max_hp,
                            'ac': character.combat_stats.armor_class
                        }
                    })
                
                except Exception as e:
                    # Send error response
                    await websocket.send_json({
                        'type': 'creation_error',
                        'error': str(e)
                    })
                    import traceback
                    print(f"Character creation error: {traceback.format_exc()}")
    
    except WebSocketDisconnect:
        print(f"Client disconnected: {connection_id}")
    except Exception as e:
        print(f"Error in WebSocket connection: {str(e)}")
        try:
            await websocket.send_json({
                'type': 'error',
                'error': str(e)
            })
        except:
            pass
    finally:
        # Clean up connection
        if connection_id in active_connections:
            del active_connections[connection_id]
        try:
            await websocket.close()
        except:
            pass

