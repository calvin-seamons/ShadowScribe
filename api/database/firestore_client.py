"""Firestore client initialization and dependency injection."""
import os
from google.cloud.firestore_v1 import AsyncClient
from typing import Optional

# Firebase project ID (different from GCP project)
FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "shadowscribe-prod-3405b")

# Singleton Firestore client
_firestore_client: Optional[AsyncClient] = None


def get_firestore_client() -> AsyncClient:
    """Get or create the Firestore async client.

    Uses the same credentials as Firebase Admin SDK (GOOGLE_APPLICATION_CREDENTIALS).
    Explicitly specifies the Firebase project ID to avoid using the wrong GCP project.
    """
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = AsyncClient(project=FIREBASE_PROJECT_ID)
    return _firestore_client


async def get_db():
    """FastAPI dependency for Firestore client.

    Yields the Firestore client for use in route handlers.
    Unlike SQLAlchemy, Firestore doesn't need session management.
    """
    yield get_firestore_client()


# Collection name constants
USERS_COLLECTION = "users"
CHARACTERS_COLLECTION = "characters"
CAMPAIGNS_COLLECTION = "campaigns"
NOTES_SUBCOLLECTION = "notes"
QUERY_LOGS_COLLECTION = "query_logs"
METADATA_COLLECTION = "metadata"
STATS_DOCUMENT = "stats"

# Backward compatibility
ROUTING_FEEDBACK_COLLECTION = QUERY_LOGS_COLLECTION
