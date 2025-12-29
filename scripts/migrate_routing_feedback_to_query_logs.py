"""
Migration script: routing_feedback -> query_logs

Migrates existing routing feedback documents to the new query_logs collection
with the updated field structure.

Usage:
    uv run python scripts/migrate_routing_feedback_to_query_logs.py --dry-run  # Preview changes
    uv run python scripts/migrate_routing_feedback_to_query_logs.py            # Execute migration
"""
import asyncio
import argparse
from datetime import datetime

from google.cloud.firestore_v1 import AsyncClient
from api.database.firestore_client import get_firestore_client


OLD_COLLECTION = "routing_feedback"
NEW_COLLECTION = "query_logs"
STATS_DOC = "metadata/stats"


async def migrate_documents(db: AsyncClient, dry_run: bool = True) -> dict:
    """Migrate documents from routing_feedback to query_logs."""
    old_collection = db.collection(OLD_COLLECTION)
    new_collection = db.collection(NEW_COLLECTION)
    
    # Get all documents from old collection
    docs = await old_collection.get()
    doc_list = list(docs)
    
    print(f"Found {len(doc_list)} documents in '{OLD_COLLECTION}'")
    
    if len(doc_list) == 0:
        print("No documents to migrate.")
        return {"migrated": 0, "skipped": 0, "errors": 0}
    
    migrated = 0
    skipped = 0
    errors = 0
    
    for doc in doc_list:
        doc_id = doc.id
        data = doc.to_dict()
        
        # Check if already exists in new collection
        new_doc = await new_collection.document(doc_id).get()
        if new_doc.exists:
            print(f"  SKIP: {doc_id} (already exists in {NEW_COLLECTION})")
            skipped += 1
            continue
        
        # Transform data - add new fields with None defaults
        migrated_data = {
            # Existing fields
            "id": data.get("id", doc_id),
            "user_query": data.get("user_query"),
            "character_name": data.get("character_name"),
            "campaign_id": data.get("campaign_id", "main_campaign"),
            "predicted_tools": data.get("predicted_tools"),
            "predicted_entities": data.get("predicted_entities"),
            "classifier_backend": data.get("classifier_backend"),
            "classifier_inference_time_ms": data.get("classifier_inference_time_ms"),
            "is_correct": data.get("is_correct"),
            "corrected_tools": data.get("corrected_tools"),
            "feedback_notes": data.get("feedback_notes"),
            "created_at": data.get("created_at"),
            "feedback_at": data.get("feedback_at"),
            "exported_for_training": data.get("exported_for_training", False),
            "exported_at": data.get("exported_at"),
            # New fields - set to None for migrated docs
            "original_query": None,
            "assistant_response": None,
            "context_sources": None,
            "response_time_ms": None,
            "model_used": None,
        }
        
        if dry_run:
            print(f"  WOULD MIGRATE: {doc_id}")
            print(f"    user_query: {data.get('user_query', '')[:50]}...")
        else:
            try:
                await new_collection.document(doc_id).set(migrated_data)
                print(f"  MIGRATED: {doc_id}")
                migrated += 1
            except Exception as e:
                print(f"  ERROR: {doc_id} - {e}")
                errors += 1
    
    return {"migrated": migrated, "skipped": skipped, "errors": errors}


async def migrate_stats(db: AsyncClient, dry_run: bool = True) -> bool:
    """Migrate stats document to use new field names."""
    stats_ref = db.document(STATS_DOC)
    stats_doc = await stats_ref.get()
    
    if not stats_doc.exists:
        print(f"No stats document found at {STATS_DOC}")
        return False
    
    old_data = stats_doc.to_dict()
    print(f"\nCurrent stats document:")
    for key, value in old_data.items():
        print(f"  {key}: {value}")
    
    # Map old field names to new ones
    new_data = {
        "queries_total": old_data.get("feedback_total", old_data.get("queries_total", 0)),
        "queries_pending": old_data.get("feedback_pending", old_data.get("queries_pending", 0)),
        "queries_correct": old_data.get("feedback_correct", old_data.get("queries_correct", 0)),
        "queries_corrected": old_data.get("feedback_corrected", old_data.get("queries_corrected", 0)),
        "queries_exported": old_data.get("feedback_exported", old_data.get("queries_exported", 0)),
    }
    
    print(f"\nNew stats document:")
    for key, value in new_data.items():
        print(f"  {key}: {value}")
    
    if dry_run:
        print("\n[DRY RUN] Would update stats document")
    else:
        await stats_ref.set(new_data)
        print("\nStats document updated!")
    
    return True


async def verify_migration(db: AsyncClient) -> None:
    """Verify migration by comparing document counts."""
    old_docs = await db.collection(OLD_COLLECTION).get()
    new_docs = await db.collection(NEW_COLLECTION).get()
    
    old_count = len(list(old_docs))
    new_count = len(list(new_docs))
    
    print(f"\nVerification:")
    print(f"  {OLD_COLLECTION}: {old_count} documents")
    print(f"  {NEW_COLLECTION}: {new_count} documents")
    
    if old_count == new_count:
        print("  ✓ Document counts match!")
    elif new_count > old_count:
        print(f"  ✓ New collection has {new_count - old_count} additional documents (new queries)")
    else:
        print(f"  ⚠ Missing {old_count - new_count} documents in new collection")


async def main():
    parser = argparse.ArgumentParser(description="Migrate routing_feedback to query_logs")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without making them")
    args = parser.parse_args()
    
    print(f"{'='*60}")
    print(f"Migration: {OLD_COLLECTION} -> {NEW_COLLECTION}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'EXECUTE'}")
    print(f"{'='*60}\n")
    
    db = get_firestore_client()
    
    # Migrate documents
    print("Step 1: Migrating documents...")
    result = await migrate_documents(db, dry_run=args.dry_run)
    print(f"\nDocument migration: {result['migrated']} migrated, {result['skipped']} skipped, {result['errors']} errors")
    
    # Migrate stats
    print("\nStep 2: Migrating stats document...")
    await migrate_stats(db, dry_run=args.dry_run)
    
    # Verify
    if not args.dry_run:
        await verify_migration(db)
    
    print(f"\n{'='*60}")
    if args.dry_run:
        print("DRY RUN complete. Run without --dry-run to execute migration.")
    else:
        print("Migration complete!")
        print(f"\nNote: The old '{OLD_COLLECTION}' collection still exists.")
        print("You can delete it manually after verifying the migration.")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
