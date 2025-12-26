import { initializeApp, getApps, FirebaseApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, Auth } from 'firebase/auth';

// Firebase configuration
// Get these values from Firebase Console > Project Settings > Your apps > Web app
const firebaseConfig = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

// Check if Firebase is configured
export const isFirebaseConfigured = () => {
    return Boolean(
        process.env.NEXT_PUBLIC_FIREBASE_API_KEY &&
        process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID
    );
};

// Lazy initialization - only initialize on first access
let _app: FirebaseApp | null = null;
let _auth: Auth | null = null;
let _googleProvider: GoogleAuthProvider | null = null;

export function getFirebaseApp(): FirebaseApp | null {
    if (typeof window === 'undefined') return null; // Don't initialize on server
    if (!isFirebaseConfigured()) return null;

    if (!_app) {
        _app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
    }
    return _app;
}

export function getFirebaseAuth(): Auth | null {
    const app = getFirebaseApp();
    if (!app) return null;

    if (!_auth) {
        _auth = getAuth(app);
    }
    return _auth;
}

export function getGoogleProvider(): GoogleAuthProvider | null {
    if (typeof window === 'undefined') return null;
    if (!isFirebaseConfigured()) return null;

    if (!_googleProvider) {
        _googleProvider = new GoogleAuthProvider();
        _googleProvider.setCustomParameters({
            prompt: 'select_account'
        });
    }
    return _googleProvider;
}

