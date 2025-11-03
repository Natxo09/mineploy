import apiClient from "@/lib/api-client";
import type {
  LoginRequest,
  TokenResponse,
  RefreshTokenRequest,
  ChangePasswordRequest,
  User,
} from "@/types";

/**
 * Authentication service
 */
export const authService = {
  /**
   * Login user
   */
  async login(data: LoginRequest): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>("/auth/login", data);
    return response.data;
  },

  /**
   * Logout user
   */
  async logout(refreshToken: string): Promise<void> {
    await apiClient.post("/auth/logout", { refresh_token: refreshToken });
  },

  /**
   * Refresh access token
   */
  async refresh(data: RefreshTokenRequest): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>("/auth/refresh", data);
    return response.data;
  },

  /**
   * Change password
   */
  async changePassword(data: ChangePasswordRequest): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>("/auth/change-password", data);
    return response.data;
  },

  /**
   * Get current user
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>("/auth/me");
    return response.data;
  },
};
