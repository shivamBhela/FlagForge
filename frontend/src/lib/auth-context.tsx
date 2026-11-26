"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { api } from "./api";

interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
}

interface Organization {
  id: string;
  name: string;
  slug: string;
  role: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  organizations: Organization[];
  currentOrg: Organization | null;
  isLoading: boolean;
  setCurrentOrg: (org: Organization) => void;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  refreshOrganizations: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentOrg, setCurrentOrg] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const loadUserData = async () => {
    try {
      const token = localStorage.getItem("ff_access_token");
      if (!token) {
        setIsLoading(false);
        return;
      }
      const profile = await api.auth.me();
      setUser(profile);

      const orgs = await api.organizations.list();
      setOrganizations(orgs);

      // Restore previously selected org or select first available
      const savedOrgId = localStorage.getItem("ff_current_org_id");
      const matched = orgs.find((o) => o.id === savedOrgId);
      if (matched) {
        setCurrentOrg(matched);
      } else if (orgs.length > 0) {
        setCurrentOrg(orgs[0]);
        localStorage.setItem("ff_current_org_id", orgs[0].id);
      }
    } catch (err) {
      localStorage.removeItem("ff_access_token");
      localStorage.removeItem("ff_refresh_token");
      setUser(null);
      setOrganizations([]);
      setCurrentOrg(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadUserData();
  }, []);

  const handleSetCurrentOrg = (org: Organization) => {
    setCurrentOrg(org);
    localStorage.setItem("ff_current_org_id", org.id);
  };

  const login = async (email: string, password: string) => {
    const tokens = await api.auth.login({ email, password });
    localStorage.setItem("ff_access_token", tokens.access_token);
    localStorage.setItem("ff_refresh_token", tokens.refresh_token);
    await loadUserData();
  };

  const register = async (email: string, password: string, fullName: string) => {
    await api.auth.register({ email, password, full_name: fullName });
    await login(email, password);
  };

  const logout = () => {
    localStorage.removeItem("ff_access_token");
    localStorage.removeItem("ff_refresh_token");
    localStorage.removeItem("ff_current_org_id");
    setUser(null);
    setOrganizations([]);
    setCurrentOrg(null);
    window.location.href = "/login";
  };

  const refreshOrganizations = async () => {
    try {
      const orgs = await api.organizations.list();
      setOrganizations(orgs);
      if (orgs.length > 0 && !currentOrg) {
        handleSetCurrentOrg(orgs[0]);
      }
    } catch (err) {
      console.error("Failed to refresh organizations", err);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        organizations,
        currentOrg,
        isLoading,
        setCurrentOrg: handleSetCurrentOrg,
        login,
        register,
        logout,
        refreshOrganizations,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
