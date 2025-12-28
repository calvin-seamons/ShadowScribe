#!/usr/bin/env python
"""
Interactive Backend Test

Tests the full RAG pipeline locally before deployment.
Uses the same code paths as the API WebSocket endpoint.

Usage:
    uv run python scripts/interactive_test.py
    uv run python scripts/interactive_test.py --character "Duskryn Nightwarden"
"""

import asyncio
import argparse
import os
import sys

# Set credentials before importing firebase
os.environ.setdefault(
    'GOOGLE_APPLICATION_CREDENTIALS',
    './credentials/firebase-service-account.json'
)

from google.cloud.firestore import AsyncClient

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dacite

from src.central_engine import CentralEngine
from src.rag.character import Character
from src.rag.context_assembler import ContextAssembler
from src.rag.session_notes import SessionNotesStorage
from src.llm.central_prompt_manager import CentralPromptManager
from api.database.firestore_client import get_firestore_client


class InteractiveTest:
    def __init__(self):
        self.db = None
        self.engine = None
        self.character = None
        self.character_name = None
        self.campaign_id = None
        self.session_storage = None

    async def initialize(self, character_name: str = None):
        """Initialize the backend systems."""
        print("\n" + "=" * 60)
        print("INTERACTIVE BACKEND TEST")
        print("=" * 60)

        # Initialize Firestore
        print("\n[1/4] Connecting to Firestore...")
        self.db = get_firestore_client()
        print("      ✓ Connected")

        # Load available characters
        print("\n[2/4] Loading characters...")
        chars = []
        async for doc in self.db.collection('characters').stream():
            data = doc.to_dict()
            chars.append({
                'id': doc.id,
                'name': data.get('name'),
                'campaign_id': data.get('campaign_id')
            })

        if not chars:
            print("      ✗ No characters found!")
            return False

        # Select character
        if character_name:
            selected = next((c for c in chars if c['name'].lower() == character_name.lower()), None)
            if not selected:
                print(f"      ✗ Character '{character_name}' not found")
                print(f"      Available: {[c['name'] for c in chars]}")
                return False
        else:
            print("      Available characters:")
            for i, c in enumerate(chars, 1):
                print(f"        {i}. {c['name']} (campaign: {c['campaign_id']})")

            while True:
                try:
                    choice = input("\n      Select character (number): ").strip()
                    idx = int(choice) - 1
                    if 0 <= idx < len(chars):
                        selected = chars[idx]
                        break
                    print("      Invalid selection")
                except ValueError:
                    print("      Enter a number")

        self.character_name = selected['name']
        self.campaign_id = selected['campaign_id']
        print(f"      ✓ Selected: {self.character_name}")

        # Load character data
        print("\n[3/4] Loading character data...")
        char_doc = await self.db.collection('characters').document(selected['id']).get()
        if char_doc.exists:
            char_data = char_doc.to_dict().get('data', {})
            config = dacite.Config(check_types=False)
            self.character = dacite.from_dict(
                data_class=Character,
                data=char_data,
                config=config
            )
            print(f"      ✓ Loaded {self.character.character_base.name}")
        else:
            print("      ✗ Could not load character data")
            return False

        # Load session notes
        print("\n[4/4] Loading session notes...")
        self.session_storage = SessionNotesStorage(self.db)
        campaign_notes = await self.session_storage.get_campaign(self.campaign_id)
        if campaign_notes:
            print(f"      ✓ Loaded {len(campaign_notes.sessions)} sessions from '{self.campaign_id}'")
            for sid, session in campaign_notes.sessions.items():
                print(f"        - Session #{session.session_number}: {session.session_name}")
        else:
            print(f"      ○ No session notes found for campaign '{self.campaign_id}'")
            campaign_notes = None

        # Initialize CentralEngine
        print("\n[*] Initializing CentralEngine...")
        context_assembler = ContextAssembler()
        prompt_manager = CentralPromptManager(context_assembler)
        self.engine = CentralEngine.create_from_config(
            prompt_manager,
            character=self.character,
            rulebook_storage=None,  # Skip rulebook for now
            campaign_session_notes=campaign_notes
        )
        print("    ✓ Ready!")

        return True

    async def query(self, user_input: str) -> str:
        """Process a query and return the response."""
        if not self.engine:
            return "Error: Engine not initialized"

        full_response = ""

        # Stream the response
        async for chunk in self.engine.process_query_stream(user_input, self.character_name):
            # Chunks can be strings (content) or dicts (metadata)
            if isinstance(chunk, str):
                print(chunk, end='', flush=True)
                full_response += chunk
            elif isinstance(chunk, dict):
                if chunk.get('type') == 'content':
                    content = chunk.get('content', '')
                    print(content, end='', flush=True)
                    full_response += content
                elif chunk.get('type') == 'routing':
                    tools = chunk.get('tools', [])
                    print(f"\n[Routing: {[t.get('tool') for t in tools]}]")
                elif chunk.get('type') == 'error':
                    print(f"\n[Error: {chunk.get('error')}]")

        print()  # Newline after response
        return full_response

    async def run_interactive(self):
        """Run the interactive loop."""
        print("\n" + "=" * 60)
        print(f"Chat with {self.character_name}")
        print("=" * 60)
        print("Type your questions. Commands:")
        print("  /quit or /exit - Exit the test")
        print("  /reload - Reload session notes from Firestore")
        print("  /sessions - Show loaded sessions")
        print("  /debug - Toggle debug mode")
        print("-" * 60 + "\n")

        debug_mode = False

        while True:
            try:
                user_input = input(f"You: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.lower() in ['/quit', '/exit', '/q']:
                    print("\nGoodbye!")
                    break

                if user_input.lower() == '/reload':
                    print("\nReloading session notes...")
                    self.session_storage.invalidate(self.campaign_id)
                    campaign_notes = await self.session_storage.get_campaign(self.campaign_id)
                    if campaign_notes:
                        context_assembler = ContextAssembler()
                        prompt_manager = CentralPromptManager(context_assembler)
                        self.engine = CentralEngine.create_from_config(
                            prompt_manager,
                            character=self.character,
                            rulebook_storage=None,
                            campaign_session_notes=campaign_notes
                        )
                        print(f"✓ Reloaded {len(campaign_notes.sessions)} sessions\n")
                    else:
                        print("○ No sessions found\n")
                    continue

                if user_input.lower() == '/sessions':
                    if self.engine.campaign_session_notes:
                        sessions = self.engine.campaign_session_notes.get_all_sessions()
                        print(f"\nLoaded {len(sessions)} sessions:")
                        for s in sessions:
                            print(f"  #{s.session_number}: {s.session_name}")
                            print(f"    NPCs: {[n.get('name') for n in s.npcs]}")
                            print(f"    Locations: {[l.get('name') for l in s.locations]}")
                    else:
                        print("\nNo sessions loaded")
                    print()
                    continue

                if user_input.lower() == '/debug':
                    debug_mode = not debug_mode
                    print(f"\nDebug mode: {'ON' if debug_mode else 'OFF'}\n")
                    continue

                # Process query
                print(f"\n{self.character_name}: ", end='')
                await self.query(user_input)
                print()

            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}\n")
                if debug_mode:
                    import traceback
                    traceback.print_exc()


async def main():
    parser = argparse.ArgumentParser(description='Interactive backend test')
    parser.add_argument('--character', '-c', help='Character name to use')
    parser.add_argument('--query', '-q', help='Single query (non-interactive)')
    args = parser.parse_args()

    test = InteractiveTest()

    if not await test.initialize(args.character):
        print("\nFailed to initialize. Exiting.")
        return

    if args.query:
        # Single query mode
        print(f"\nQuery: {args.query}")
        print(f"\n{test.character_name}: ", end='')
        await test.query(args.query)
    else:
        # Interactive mode
        await test.run_interactive()


if __name__ == '__main__':
    asyncio.run(main())
