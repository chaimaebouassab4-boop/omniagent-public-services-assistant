import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode
} from "react";
import { login as loginRequest } from "../services/auth";
import { tokenStorage } from "../services/tokenStorage";
import type { LoginPayload, User } from "../types/api";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

/** Provides JWT-backed administrator authentication state to the app. */
export function AuthProvider({ children }: AuthProviderProps): JSX.Element {
  const [token, setToken] = useState<string | null>(() => tokenStorage.getToken());
  const [user, setUser] = useState<User | null>(() => tokenStorage.getUser());

  const login = useCallback(async (payload: LoginPayload) => {
    const result = await loginRequest(payload);
    tokenStorage.setToken(result.tokens.accessToken);
    tokenStorage.setUser(result.user);
    setToken(result.tokens.accessToken);
    setUser(result.user);
  }, []);

  const logout = useCallback(() => {
    tokenStorage.clear();
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token && user),
      isAdmin: Boolean(user?.isAdmin),
      login,
      logout
    }),
    [login, logout, token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/** Reads the current authentication context. */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
