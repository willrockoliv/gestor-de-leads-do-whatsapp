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
  const [token, setTokenState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const setToken = useCallback((t: string) => {
    localStorage.setItem("token", t);
    setTokenState(t);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    setTokenState(null);
    setUser(null);
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem("token");
    console.log("[auth-context] useEffect (token load)", { stored });
    if (stored) {
      setTokenState(stored);
    } else {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    console.log("[auth-context] useEffect (token)", { token });
    if (!token) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    getMe()
      .then((user) => {
        console.log("[auth-context] getMe() success", user);
        setUser(user);
      })
      .catch((err) => {
        console.error("[auth-context] getMe() error", err);
        logout();
      })
      .finally(() => {
        setIsLoading(false);
        console.log("[auth-context] isLoading set to false");
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
