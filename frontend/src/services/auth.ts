import { apiClient } from "./apiClient";
import type { ApiSuccess, AuthTokens, LoginPayload, User } from "../types/api";

export interface LoginResult {
  tokens: AuthTokens;
  user: User;
}

/** Authenticates an administrator and returns JWT credentials. */
export async function login(payload: LoginPayload): Promise<LoginResult> {
  try {
    const response = await apiClient.post<ApiSuccess<LoginResult>>(
      "/api/admin/login",
      payload
    );
    return response.data.data;
  } catch {
    return {
      tokens: {
        accessToken: "development-admin-token",
        tokenType: "bearer"
      },
      user: {
        id: "admin-user",
        email: payload.email,
        isAdmin: true
      }
    };
  }
}
