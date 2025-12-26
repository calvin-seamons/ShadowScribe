"""Database connection - re-exports Firestore client for backward compatibility."""
from api.database.firestore_client import get_db, get_firestore_client

__all__ = ['get_db', 'get_firestore_client']
