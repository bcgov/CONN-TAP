"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

interface AuthenticatedSession {
  authenticated: true;
  subject: string;
  username: string | null;
  email: string | null;
  name: string | null;
  expiresAt: string;
}

interface AnonymousSession {
  authenticated: false;
}

type SessionResponse = AuthenticatedSession | AnonymousSession;

interface AuthContextType {
  isAuthenticated: boolean;
  username: string | null;
  loading: boolean;
  session: AuthenticatedSession | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthenticatedSession | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    fetch("/auth/session", { credentials: "same-origin", cache: "no-store" })
      .then((response) => (response.ok ? response.json() : { authenticated: false }))
      .then((data: SessionResponse) => {
        if (!mounted) return;
        setSession(data.authenticated ? data : null);
      })
      .catch(() => {
        if (mounted) setSession(null);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: Boolean(session),
        username: session?.username ?? session?.name ?? null,
        loading,
        session,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
