#!/usr/bin/env python3
"""
Migrate data from Cloud SQL (MySQL) to Firestore.

Usage:
    uv run python scripts/migrate_to_firestore.py

Requirements:
    - Cloud SQL Proxy running on port 3307
    - GOOGLE_APPLICATION_CREDENTIALS set for Firestore
"""
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from google.cloud import firestore

# Cloud SQL connection (via proxy)
MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3307
MYSQL_USER = "root"
MYSQL_PASSWORD = "E9UkfdUsBuwjEZwWqCk3TmSZ"
MYSQL_DATABASE = "shadowscribe"

# Firestore collections
USERS_COLLECTION = "users"
CHARACTERS_COLLECTION = "characters"
CAMPAIGNS_COLLECTION = "campaigns"
ROUTING_FEEDBACK_COLLECTION = "routing_feedback"
METADATA_COLLECTION = "metadata"
STATS_DOCUMENT = "stats"


def get_mysql_connection():
    """Get MySQL connection to Cloud SQL."""
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        cursorclass=pymysql.cursors.DictCursor
    )


def migrate_users(mysql_conn, firestore_db):
    """Migrate users from MySQL to Firestore."""
    print("\n📦 Migrating users...")

    with mysql_conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

    migrated = 0
    for user in users:
        doc_ref = firestore_db.collection(USERS_COLLECTION).document(user['id'])
        doc_ref.set({
            'email': user['email'],
            'display_name': user.get('display_name'),
            'created_at': user.get('created_at') or datetime.utcnow()
        })
        migrated += 1
        print(f"  ✓ User: {user['email']}")

    print(f"  Total: {migrated} users migrated")
    return migrated


def migrate_campaigns(mysql_conn, firestore_db):
    """Migrate campaigns from MySQL to Firestore."""
    print("\n📦 Migrating campaigns...")

    with mysql_conn.cursor() as cursor:
        cursor.execute("SELECT * FROM campaigns")
        campaigns = cursor.fetchall()

    migrated = 0
    for campaign in campaigns:
        doc_ref = firestore_db.collection(CAMPAIGNS_COLLECTION).document(campaign['id'])
        doc_ref.set({
            'name': campaign['name'],
            'description': campaign.get('description'),
            'created_at': campaign.get('created_at') or datetime.utcnow()
        })
        migrated += 1
        print(f"  ✓ Campaign: {campaign['name']}")

    print(f"  Total: {migrated} campaigns migrated")
    return migrated


def migrate_characters(mysql_conn, firestore_db):
    """Migrate characters from MySQL to Firestore."""
    print("\n📦 Migrating characters...")

    with mysql_conn.cursor() as cursor:
        cursor.execute("SELECT * FROM characters")
        characters = cursor.fetchall()

    migrated = 0
    for char in characters:
        doc_ref = firestore_db.collection(CHARACTERS_COLLECTION).document(char['id'])

        # Parse JSON data if it's a string
        data = char.get('data', {})
        if isinstance(data, str):
            import json
            data = json.loads(data)

        doc_ref.set({
            'user_id': char['user_id'],
            'campaign_id': char.get('campaign_id'),
            'name': char['name'],
            'race': char.get('race'),
            'character_class': char.get('character_class'),
            'level': char.get('level'),
            'data': data,
            'created_at': char.get('created_at') or datetime.utcnow(),
            'updated_at': char.get('updated_at') or datetime.utcnow()
        })
        migrated += 1
        print(f"  ✓ Character: {char['name']}")

    print(f"  Total: {migrated} characters migrated")
    return migrated


def migrate_session_notes(mysql_conn, firestore_db):
    """Migrate session notes from MySQL to Firestore (as subcollections)."""
    print("\n📦 Migrating session notes...")

    with mysql_conn.cursor() as cursor:
        cursor.execute("SELECT * FROM session_notes")
        notes = cursor.fetchall()

    migrated = 0
    for note in notes:
        # Notes are stored as subcollections under campaigns
        campaign_ref = firestore_db.collection(CAMPAIGNS_COLLECTION).document(note['campaign_id'])
        note_ref = campaign_ref.collection('notes').document(note['id'])

        # Parse processed_content if it's a string
        processed = note.get('processed_content')
        if isinstance(processed, str):
            import json
            try:
                processed = json.loads(processed)
            except:
                processed = None

        note_ref.set({
            'user_id': note['user_id'],
            'content': note['content'],
            'processed_content': processed,
            'created_at': note.get('created_at') or datetime.utcnow()
        })
        migrated += 1
        print(f"  ✓ Note in campaign {note['campaign_id'][:8]}...")

    print(f"  Total: {migrated} notes migrated")
    return migrated


def migrate_routing_feedback(mysql_conn, firestore_db):
    """Migrate routing feedback from MySQL to Firestore."""
    print("\n📦 Migrating routing feedback...")

    with mysql_conn.cursor() as cursor:
        cursor.execute("SELECT * FROM routing_feedback")
        records = cursor.fetchall()

    # Track stats for counter initialization
    stats = {
        'total': 0,
        'pending': 0,
        'correct': 0,
        'corrected': 0,
        'exported': 0
    }

    migrated = 0
    for record in records:
        doc_ref = firestore_db.collection(ROUTING_FEEDBACK_COLLECTION).document(record['id'])

        # Parse JSON fields if they're strings
        predicted_tools = record.get('predicted_tools', [])
        if isinstance(predicted_tools, str):
            import json
            predicted_tools = json.loads(predicted_tools)

        predicted_entities = record.get('predicted_entities')
        if isinstance(predicted_entities, str):
            import json
            try:
                predicted_entities = json.loads(predicted_entities)
            except:
                predicted_entities = None

        corrected_tools = record.get('corrected_tools')
        if isinstance(corrected_tools, str):
            import json
            try:
                corrected_tools = json.loads(corrected_tools)
            except:
                corrected_tools = None

        doc_ref.set({
            'user_query': record['user_query'],
            'character_name': record['character_name'],
            'campaign_id': record.get('campaign_id', 'main_campaign'),
            'predicted_tools': predicted_tools,
            'predicted_entities': predicted_entities,
            'classifier_backend': record.get('classifier_backend', 'local'),
            'classifier_inference_time_ms': record.get('classifier_inference_time_ms'),
            'is_correct': record.get('is_correct'),
            'corrected_tools': corrected_tools,
            'feedback_notes': record.get('feedback_notes'),
            'created_at': record.get('created_at') or datetime.utcnow(),
            'feedback_at': record.get('feedback_at'),
            'exported_for_training': record.get('exported_for_training', False),
            'exported_at': record.get('exported_at')
        })

        # Update stats
        stats['total'] += 1
        if record.get('is_correct') is None:
            stats['pending'] += 1
        elif record.get('is_correct') == True:
            stats['correct'] += 1
        elif record.get('is_correct') == False and corrected_tools:
            stats['corrected'] += 1

        if record.get('exported_for_training'):
            stats['exported'] += 1

        migrated += 1
        print(f"  ✓ Feedback: {record['user_query'][:40]}...")

    print(f"  Total: {migrated} feedback records migrated")
    return migrated, stats


def initialize_stats_document(firestore_db, stats):
    """Initialize the stats counter document."""
    print("\n📊 Initializing stats counter document...")

    stats_ref = firestore_db.collection(METADATA_COLLECTION).document(STATS_DOCUMENT)
    stats_ref.set({
        'feedback_total': stats['total'],
        'feedback_pending': stats['pending'],
        'feedback_correct': stats['correct'],
        'feedback_corrected': stats['corrected'],
        'feedback_exported': stats['exported']
    })

    print(f"  ✓ Stats: total={stats['total']}, pending={stats['pending']}, correct={stats['correct']}, corrected={stats['corrected']}")


def main():
    """Run the migration."""
    print("=" * 60)
    print("🚀 Cloud SQL to Firestore Migration")
    print("=" * 60)

    # Check for credentials
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        print("   Set it to your Firebase service account JSON file")
        sys.exit(1)

    print(f"\n📌 Using credentials: {creds_path}")
    print(f"📌 MySQL: {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")

    # Connect to MySQL
    print("\n🔌 Connecting to Cloud SQL...")
    try:
        mysql_conn = get_mysql_connection()
        print("  ✓ Connected to MySQL")
    except Exception as e:
        print(f"  ❌ Failed to connect to MySQL: {e}")
        print("     Is the Cloud SQL Proxy running?")
        sys.exit(1)

    # Connect to Firestore
    print("\n🔌 Connecting to Firestore...")
    try:
        firestore_db = firestore.Client()
        print(f"  ✓ Connected to Firestore project: {firestore_db.project}")
    except Exception as e:
        print(f"  ❌ Failed to connect to Firestore: {e}")
        sys.exit(1)

    try:
        # Migrate data in order
        users_count = migrate_users(mysql_conn, firestore_db)
        campaigns_count = migrate_campaigns(mysql_conn, firestore_db)
        characters_count = migrate_characters(mysql_conn, firestore_db)
        notes_count = migrate_session_notes(mysql_conn, firestore_db)
        feedback_count, feedback_stats = migrate_routing_feedback(mysql_conn, firestore_db)

        # Initialize stats document
        initialize_stats_document(firestore_db, feedback_stats)

        # Summary
        print("\n" + "=" * 60)
        print("✅ Migration Complete!")
        print("=" * 60)
        print(f"   Users:     {users_count}")
        print(f"   Campaigns: {campaigns_count}")
        print(f"   Characters: {characters_count}")
        print(f"   Notes:     {notes_count}")
        print(f"   Feedback:  {feedback_count}")
        print("\n🎉 Data successfully migrated to Firestore!")
        print("\n⚠️  Next steps:")
        print("   1. Test the API with Firestore")
        print("   2. If everything works, delete Cloud SQL instance")
        print("   3. Remove SQLAlchemy dependencies from pyproject.toml")

    finally:
        mysql_conn.close()


if __name__ == "__main__":
    main()
