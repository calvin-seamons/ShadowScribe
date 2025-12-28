"""
Migrate session notes from notes/ subcollection to sessions/ subcollection.

This is a one-time migration script to transform the old session note structure
to the new unified SessionDocument model.

Usage:
    uv run python scripts/migrate_session_notes.py --dry-run    # Preview changes
    uv run python scripts/migrate_session_notes.py              # Execute migration
    uv run python scripts/migrate_session_notes.py --fail-fast  # Abort on first error
"""

import asyncio
import argparse
import os
from datetime import datetime, timezone

# Set credentials before importing firebase
os.environ.setdefault(
    'GOOGLE_APPLICATION_CREDENTIALS',
    './credentials/firebase-service-account.json'
)

from google.cloud.firestore import AsyncClient  # For type hints only
from api.database.firestore_client import get_firestore_client
from api.database.firestore_models import SessionDocument


async def get_all_campaigns(db: AsyncClient) -> list[dict]:
    """Get all campaigns from Firestore."""
    campaigns = []
    async for doc in db.collection('campaigns').stream():
        campaigns.append({
            'id': doc.id,
            'data': doc.to_dict()
        })
    return campaigns


async def get_notes_for_campaign(db: AsyncClient, campaign_id: str) -> list[dict]:
    """Get all notes from the old notes/ subcollection."""
    notes = []
    notes_ref = db.collection('campaigns').document(campaign_id).collection('notes')
    async for doc in notes_ref.stream():
        notes.append({
            'id': doc.id,
            'data': doc.to_dict()
        })
    return notes


async def check_sessions_exist(db: AsyncClient, campaign_id: str) -> list[str]:
    """Check if sessions already exist in the sessions/ subcollection."""
    session_ids = []
    sessions_ref = db.collection('campaigns').document(campaign_id).collection('sessions')
    async for doc in sessions_ref.stream():
        session_ids.append(doc.id)
    return session_ids


def transform_note_to_session(note_id: str, campaign_id: str, note_data: dict) -> SessionDocument:
    """Transform old note format to new SessionDocument format."""
    # Map old fields to new fields
    session_number = note_data.get('session_number', 0)
    title = note_data.get('title', '')

    # Use title as session_name, fallback to "Session {number}"
    session_name = title if title else f"Session {session_number}"

    return SessionDocument(
        id=note_id,
        campaign_id=campaign_id,
        user_id=note_data.get('user_id', ''),
        session_number=session_number,
        session_name=session_name,

        # Content fields
        raw_content=note_data.get('raw_notes', ''),
        processed_markdown=note_data.get('content', ''),
        title=title,
        summary=note_data.get('summary', ''),

        # Entity lists - empty, to be populated by processing
        player_characters=[],
        npcs=[],
        locations=[],
        items=[],

        # Structured fields - empty, to be populated by processing
        key_events=[],
        combat_encounters=[],
        spells_abilities_used=[],
        character_decisions=[],
        character_statuses={},
        memories_visions=[],
        quest_updates=[],
        loot_obtained={},
        deaths=[],
        revivals=[],
        party_conflicts=[],
        party_bonds=[],
        quotes=[],
        funny_moments=[],
        puzzles_encountered={},
        mysteries_revealed=[],
        unresolved_questions=[],
        divine_interventions=[],
        religious_elements=[],
        rules_clarifications=[],
        dice_rolls=[],
        cliffhanger=None,
        next_session_hook=None,
        dm_notes=[],
        raw_sections={},

        # Timestamps
        date=note_data.get('session_date'),
        created_at=note_data.get('created_at'),
        updated_at=datetime.now(timezone.utc),
    )


async def migrate_campaign(db: AsyncClient, campaign_id: str, *, dry_run: bool = False, fail_fast: bool = False) -> dict:
    """Migrate a single campaign's notes to sessions.
    
    Args:
        db: Firestore client
        campaign_id: Campaign to migrate
        dry_run: If True, preview changes without writing
        fail_fast: If True, re-raise exceptions instead of continuing
    """
    result = {
        'campaign_id': campaign_id,
        'notes_found': 0,
        'sessions_created': 0,
        'skipped': 0,
        'errors': []
    }

    # Get existing notes
    notes = await get_notes_for_campaign(db, campaign_id)
    result['notes_found'] = len(notes)

    if not notes:
        print(f"  No notes found in {campaign_id}/notes/")
        return result

    # Check for existing sessions
    existing_sessions = await check_sessions_exist(db, campaign_id)

    for note in notes:
        note_id = note['id']
        note_data = note['data']

        # Skip if session already exists
        if note_id in existing_sessions:
            print(f"  Skipping {note_id} - session already exists")
            result['skipped'] += 1
            continue

        try:
            # Transform to SessionDocument
            session = transform_note_to_session(note_id, campaign_id, note_data)

            if dry_run:
                print(f"  [DRY RUN] Would create session: {session.session_name} (#{session.session_number})")
                print(f"    - raw_content: {len(session.raw_content or '')} chars")
                print(f"    - processed_markdown: {len(session.processed_markdown or '')} chars")
                print(f"    - summary: {len(session.summary or '')} chars")
            else:
                # Write to sessions/ subcollection
                sessions_ref = db.collection('campaigns').document(campaign_id).collection('sessions')
                await sessions_ref.document(note_id).set(session.to_dict())
                print(f"  Created session: {session.session_name} (#{session.session_number})")

            result['sessions_created'] += 1

        except Exception as e:
            error_msg = f"Error migrating note {note_id}: {e!r}"
            print(f"  ERROR: {error_msg}")
            result['errors'].append(error_msg)
            if fail_fast:
                raise

    return result


async def main(*, dry_run: bool = True, fail_fast: bool = False):
    """Main migration function."""
    print("=" * 60)
    print("Session Notes Migration: notes/ -> sessions/")
    print("=" * 60)

    if dry_run:
        print("\n*** DRY RUN MODE - No changes will be made ***\n")
    else:
        print("\n*** LIVE MODE - Changes will be written to Firestore ***\n")

    # Initialize Firestore (using centralized singleton)
    db = get_firestore_client()

    # Get all campaigns
    campaigns = await get_all_campaigns(db)
    print(f"Found {len(campaigns)} campaigns\n")

    total_results = {
        'campaigns_processed': 0,
        'total_notes': 0,
        'total_sessions_created': 0,
        'total_skipped': 0,
        'total_errors': []
    }

    for campaign in campaigns:
        campaign_id = campaign['id']
        campaign_name = campaign['data'].get('name', campaign_id)
        print(f"\nProcessing campaign: {campaign_name} ({campaign_id})")
        print("-" * 40)

        result = await migrate_campaign(db, campaign_id, dry_run=dry_run, fail_fast=fail_fast)

        total_results['campaigns_processed'] += 1
        total_results['total_notes'] += result['notes_found']
        total_results['total_sessions_created'] += result['sessions_created']
        total_results['total_skipped'] += result['skipped']
        total_results['total_errors'].extend(result['errors'])

    # Print summary
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Campaigns processed: {total_results['campaigns_processed']}")
    print(f"Total notes found: {total_results['total_notes']}")
    print(f"Sessions created: {total_results['total_sessions_created']}")
    print(f"Skipped (already exist): {total_results['total_skipped']}")
    print(f"Errors: {len(total_results['total_errors'])}")

    if total_results['total_errors']:
        print("\nErrors:")
        for error in total_results['total_errors']:
            print(f"  - {error}")

    if dry_run:
        print("\n*** This was a dry run. Run without --dry-run to execute. ***")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Migrate session notes to new structure')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing')
    parser.add_argument('--fail-fast', action='store_true', help='Abort on first error instead of continuing')
    args = parser.parse_args()

    asyncio.run(main(dry_run=args.dry_run, fail_fast=args.fail_fast))
