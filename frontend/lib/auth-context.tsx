'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import {
    User as FirebaseUser,
    signInWithPopup,
    signOut as firebaseSignOut,
    onAuthStateChanged
} from 'firebase/auth';
import { getFirebaseAuth, getGoogleProvider, isFirebaseConfigured } from './firebase';

// Types
interface User {
    uid: string;
    email: string;
    displayName: string | null;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    loading: boolean;
    signIn: () => Promise<void>;
    signOut: () => void;
    isAuthenticated: boolean;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // If Firebase is not configured, use demo mode
        if (!isFirebaseConfigured()) {
            console.log('[Auth] Firebase not configured, using demo mode');
            const storedUser = localStorage.getItem('auth_user');
            const storedToken = localStorage.getItem('auth_token');

            if (storedUser && storedToken) {
                setUser(JSON.parse(storedUser));
                setToken(storedToken);
            }
            setLoading(false);
            return;
        }

        const auth = getFirebaseAuth();
        if (!auth) {
            setLoading(false);
            return;
        }

        // Firebase auth state listener
        const unsubscribe = onAuthStateChanged(auth, async (firebaseUser: FirebaseUser | null) => {
            if (firebaseUser) {
                const idToken = await firebaseUser.getIdToken();
                const userData: User = {
                    uid: firebaseUser.uid,
                    email: firebaseUser.email || '',
                    displayName: firebaseUser.displayName
                };
                setUser(userData);
                setToken(idToken);

                // Store for persistence across page reloads
                localStorage.setItem('auth_user', JSON.stringify(userData));
                localStorage.setItem('auth_token', idToken);
            } else {
                setUser(null);
                setToken(null);
                localStorage.removeItem('auth_user');
                localStorage.removeItem('auth_token');
            }
            setLoading(false);
        });

        return () => unsubscribe();
    }, []);

    // Refresh token periodically (Firebase tokens expire after 1 hour)
    useEffect(() => {
        if (!isFirebaseConfigured() || !user) return;

        const auth = getFirebaseAuth();
        if (!auth) return;

        const refreshToken = async () => {
            const currentUser = auth.currentUser;
            if (currentUser) {
                const newToken = await currentUser.getIdToken(true);
                setToken(newToken);
                localStorage.setItem('auth_token', newToken);
            }
        };

        // Refresh every 50 minutes
        const interval = setInterval(refreshToken, 50 * 60 * 1000);
        return () => clearInterval(interval);
    }, [user]);

    const signIn = async () => {
        setLoading(true);

        if (!isFirebaseConfigured()) {
            // Demo mode sign in
            await new Promise(resolve => setTimeout(resolve, 500));
            const demoUser: User = {
                uid: 'demo-user-' + Date.now(),
                email: 'demo@shadowscribe.app',
                displayName: 'Demo Player'
            };
            const payload = {
                uid: demoUser.uid,
                sub: demoUser.uid,
                email: demoUser.email,
                name: demoUser.displayName,
                iat: Math.floor(Date.now() / 1000),
                exp: Math.floor(Date.now() / 1000) + 3600
            };
            const mockToken = 'header.' + btoa(JSON.stringify(payload)) + '.signature';

            setUser(demoUser);
            setToken(mockToken);
            localStorage.setItem('auth_user', JSON.stringify(demoUser));
            localStorage.setItem('auth_token', mockToken);
            setLoading(false);
            return;
        }

        const auth = getFirebaseAuth();
        const provider = getGoogleProvider();

        if (!auth || !provider) {
            console.error('[Auth] Firebase not initialized');
            setLoading(false);
            return;
        }

        try {
            await signInWithPopup(auth, provider);
            // onAuthStateChanged will handle the rest
        } catch (error) {
            console.error('[Auth] Sign in error:', error);
            setLoading(false);
            throw error;
        }
    };

    const signOut = async () => {
        const auth = getFirebaseAuth();
        if (isFirebaseConfigured() && auth) {
            await firebaseSignOut(auth);
        }
        setUser(null);
        setToken(null);
        localStorage.removeItem('auth_user');
        localStorage.removeItem('auth_token');
    };

    const value: AuthContextType = {
        user,
        token,
        loading,
        signIn,
        signOut,
        isAuthenticated: !!user && !!token
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

// Hook to use auth context
export function useAuth(): AuthContextType {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

// HOC for protected routes
export function withAuth<P extends object>(
    WrappedComponent: React.ComponentType<P>
): React.FC<P> {
    return function AuthenticatedComponent(props: P) {
        const { isAuthenticated, loading } = useAuth();

        if (loading) {
            return (
                <div className="flex items-center justify-center min-h-screen">
                    <div className="text-lg">Loading...</div>
                </div>
            );
        }

        if (!isAuthenticated) {
            return (
                <div className="flex items-center justify-center min-h-screen">
                    <div className="text-center">
                        <h2 className="text-xl mb-4">Authentication Required</h2>
                        <p className="text-gray-500">Please sign in to access this page.</p>
                    </div>
                </div>
            );
        }

        return <WrappedComponent {...props} />;
    };
}
