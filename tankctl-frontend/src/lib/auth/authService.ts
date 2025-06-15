// lib/auth/authService.ts

import { getToken, setToken, removeToken } from "@/lib/auth/tokenStorage";
import { post, setApiBaseUrl } from "@/lib/api/apiClient"; // Import post and setApiBaseUrl

interface AuthResponse {
  success: boolean;
  token?: string;
  message?: string;
}

// Function to handle login
export async function login(apiUrl: string, apiKey: string): Promise<AuthResponse> {
  try {
    setApiBaseUrl(apiUrl); // Set the API base URL dynamically

    const response = await post<{ access_token: string }>("/api/v1/auth/token", {
      username: "admin",
      password: apiKey,
    }, "application/x-www-form-urlencoded"); // Specify content type

    console.log('Response from apiClient.post in authService:', {
      success: response.success,
      accessToken: response.data?.access_token,
      fullData: response.data,
      error: response.error,
    });

    if (response.success && response.data?.access_token) {
      setToken(response.data.access_token);
      return { success: true, token: response.data.access_token };
    } else {
      return { success: false, message: response.error || "Authentication failed." };
    }
  } catch (error: any) {
    return { success: false, message: error.message || "An unexpected error occurred during login." };
  }
}

// Function to handle logout
export function logout(): void {
  removeToken();
  // In a real app, you might redirect the user here
  // For now, simply clear the token.
}

// Function to check if user is authenticated (e.g., by validating JWT)
export function isAuthenticated(): boolean {
  const token = getToken();
  // In a real application, you would also validate the token (e.g., check expiration)
  return !!token;
}