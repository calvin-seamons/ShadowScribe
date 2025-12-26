"""Firebase Authentication utilities for ShadowScribe API."""
import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.cloud.firestore_v1 import AsyncClient

from api.database.firestore_client import get_db, USERS_COLLECTION
from api.database.firestore_models import UserDocument

# Firebase Admin SDK (optional - for server-side verification)
# If firebase-admin is not installed, we'll use a simpler approach
try:
    import firebase_admin
    from firebase_admin import auth as firebase_auth, credentials

    # Initialize Firebase Admin if not already done
    if not firebase_admin._apps:
        # Try to use default credentials or a service account file
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            # Use default credentials (works on Cloud Run with proper IAM)
            firebase_admin.initialize_app()

    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("[Auth] firebase-admin not installed. Using simplified auth.")


# Security scheme
security = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    """Represents an authenticated user."""
    def __init__(self, uid: str, email: str, display_name: Optional[str] = None):
        self.uid = uid
        self.email = email
        self.display_name = display_name


async def verify_firebase_token(token: str) -> Optional[dict]:
    """Verify a Firebase ID token and return the decoded claims."""
    if not FIREBASE_AVAILABLE:
        raise RuntimeError("Firebase Admin SDK not available - cannot verify tokens")

    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except firebase_auth.InvalidIdTokenError as e:
        print(f"[Auth] Invalid token: {e}")
        return None
    except firebase_auth.ExpiredIdTokenError as e:
        print(f"[Auth] Expired token: {e}")
        return None
    except firebase_auth.RevokedIdTokenError as e:
        print(f"[Auth] Revoked token: {e}")
        return None


async def get_or_create_user(
    db: AsyncClient,
    uid: str,
    email: str,
    display_name: Optional[str] = None
) -> UserDocument:
    """Get existing user or create a new one in Firestore."""
    users_collection = db.collection(USERS_COLLECTION)
    user_ref = users_collection.document(uid)

    # Try to find existing user
    user_doc = await user_ref.get()

    if user_doc.exists:
        return UserDocument.from_firestore(user_doc.id, user_doc.to_dict())

    # Create new user
    user = UserDocument(
        id=uid,
        email=email,
        display_name=display_name
    )

    await user_ref.set(user.to_dict())

    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncClient = Depends(get_db)
) -> UserDocument:
    """
    FastAPI dependency to get the current authenticated user.

    Extracts and verifies the Firebase ID token from the Authorization header,
    then returns the corresponding UserDocument from Firestore.

    Raises:
        HTTPException: If no token provided or token is invalid.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    decoded = await verify_firebase_token(token)

    if not decoded:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user info from token
    uid = decoded.get("uid") or decoded.get("sub")
    email = decoded.get("email", "")
    display_name = decoded.get("name")

    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
        )

    # Get or create user in Firestore
    user = await get_or_create_user(db, uid, email, display_name)

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncClient = Depends(get_db)
) -> Optional[UserDocument]:
    """
    FastAPI dependency for optional authentication.

    Returns the authenticated user if a valid token is provided,
    or None if no token is provided. Raises exception only for invalid tokens.
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
