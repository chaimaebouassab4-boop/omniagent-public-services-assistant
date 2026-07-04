import type { User } from "../types/api";

const TOKEN_KEY = "omniagent.accessToken";
const USER_KEY = "omniagent.user";

/** Persists and reads JWT authentication state from localStorage. */
export const tokenStorage = {
  getToken(): string | null {
    return window.localStorage.getItem(TOKEN_KEY);
  },
  setToken(token: string): void {
    window.localStorage.setItem(TOKEN_KEY, token);
  },
  getUser(): User | null {
    const raw = window.localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  },
  setUser(user: User): void {
    window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  clear(): void {
    window.localStorage.removeItem(TOKEN_KEY);
    window.localStorage.removeItem(USER_KEY);
  }
};
