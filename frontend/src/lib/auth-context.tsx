"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { getMe, type UserResponse } from "@/lib/api";

interface AuthContextType {
  user: UserResponse | null;
  token: string | null;
  isLoading: boolean;
  setToken: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [token, setTokenState] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("token");
  });
  const [isLoading, setIsLoading] = useState<boolean>(() => {
    if (typeof window === "undefined") return true;
    return !!localStorage.getItem("token");
  });

  const setToken = useCallback((t: string) => {
    localStorage.setItem("token", t);
    setIsLoading(true);
    setTokenState(t);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    setTokenState(null);
    setUser(null);
    setIsLoading(false);
  }, []);

  useEffect(() => {
    if (!token) return;

    getMe()
      .then((user) => {
        setUser(user);
      })
      .catch((err) => {
        console.error("[auth-context] getMe() error", err);
        logout();
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [token, logout]);

  return (
    <AuthContext.Provider value={{ user, token, isLoading, setToken, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
