"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  clearance: string;
  organization: string;
  avatarUrl?: string;
  provider: "password" | "google";
  lastLogin: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signup: (name: string, email: string, password: string, role?: string) => Promise<{ success: boolean; error?: string }>;
  loginWithGoogle: () => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  updateUser: (data: Partial<User>) => void;
}

const DEFAULT_USER: User = {
  id: "usr-01",
  name: "Shivangi Mohanty",
  email: "shivangi.mohanty@geointel.ai",
  role: "Senior Intelligence Analyst",
  clearance: "Level 4 (Top Secret / SCI)",
  organization: "Global Threat Assessment Directorate",
  provider: "password",
  lastLogin: "Active Now",
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = "geointel_auth_session";

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize from localStorage or fallback to default authenticated user
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setUser(JSON.parse(stored));
      } else {
        // Set default initial user so dashboard is immediately usable
        setUser(DEFAULT_USER);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_USER));
      }
    } catch {
      setUser(DEFAULT_USER);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    setIsLoading(true);
    await new Promise((r) => setTimeout(r, 600)); // Realistic network latency

    if (!email || !email.includes("@")) {
      setIsLoading(false);
      return { success: false, error: "Please enter a valid intelligence agency email address." };
    }

    if (!password || password.length < 6) {
      setIsLoading(false);
      return { success: false, error: "Password must be at least 6 characters." };
    }

    // Extract plausible name from email if not already matching
    const inferredName = email.split("@")[0].replace(/[._]/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());

    const loggedInUser: User = {
      id: "usr-" + Math.floor(1000 + Math.random() * 9000),
      name: inferredName || "Analyst",
      email: email.trim(),
      role: "Strategic Intelligence Analyst",
      clearance: "Level 4 (Top Secret)",
      organization: "Defense Geopolitical Directorate",
      provider: "password",
      lastLogin: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setUser(loggedInUser);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(loggedInUser));
    setIsLoading(false);
    return { success: true };
  };

  const signup = async (
    name: string,
    email: string,
    password: string,
    role = "Senior Intelligence Analyst"
  ): Promise<{ success: boolean; error?: string }> => {
    setIsLoading(true);
    await new Promise((r) => setTimeout(r, 700));

    if (!name.trim()) {
      setIsLoading(false);
      return { success: false, error: "Full Name is required." };
    }
    if (!email || !email.includes("@")) {
      setIsLoading(false);
      return { success: false, error: "Please provide a valid intelligence email address." };
    }
    if (!password || password.length < 6) {
      setIsLoading(false);
      return { success: false, error: "Password must be at least 6 characters." };
    }

    const newUser: User = {
      id: "usr-" + Math.floor(1000 + Math.random() * 9000),
      name: name.trim(),
      email: email.trim(),
      role: role.trim(),
      clearance: "Level 4 (Special Intelligence)",
      organization: "Global Risk & Geopolitical Affairs",
      provider: "password",
      lastLogin: "Just now",
    };

    setUser(newUser);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newUser));
    setIsLoading(false);
    return { success: true };
  };

  const loginWithGoogle = async (): Promise<{ success: boolean; error?: string }> => {
    setIsLoading(true);
    await new Promise((r) => setTimeout(r, 800)); // Simulate Google OAuth handshake

    const googleUser: User = {
      id: "goog-usr-" + Math.floor(1000 + Math.random() * 9000),
      name: "Shivangi Mohanty",
      email: "shivangi.mohanty@gmail.com",
      role: "Geopolitical Intelligence Strategist",
      clearance: "Verified Google Enterprise SSO (Level 3)",
      organization: "GeoIntelligence Command",
      avatarUrl: "https://lh3.googleusercontent.com/a/default-user=s96-c",
      provider: "google",
      lastLogin: "Active via Google SSO",
    };

    setUser(googleUser);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(googleUser));
    setIsLoading(false);
    return { success: true };
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
    router.push("/login");
  };

  const updateUser = (data: Partial<User>) => {
    if (!user) return;
    const updated = { ...user, ...data };
    setUser(updated);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        signup,
        loginWithGoogle,
        logout,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
