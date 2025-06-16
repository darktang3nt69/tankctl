import { getToken } from "@/lib/auth/tokenStorage";
import { toast } from 'sonner';

interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  status?: number;
}

let API_BASE_URL = ""; // This will be dynamically set by the login form

export function setApiBaseUrl(url: string) {
  API_BASE_URL = url;
}

// Function to make authenticated GET requests
export async function get<T>(path: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
  const token = getToken();
  const url = new URL(`${API_BASE_URL}${path}`);

  if (params) {
    Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));
  }

  try {
    const response = await fetch(url.toString(), {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        ...(token && { "Authorization": `Bearer ${token}` }),
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      return { success: false, error: errorText || response.statusText, status: response.status };
    }

    const data = await response.json();
    return { success: true, data };
  } catch (error: any) {
    const errorMessage = error.message || "Network error or API is unreachable.";
    toast.error(`API Error: ${errorMessage}`);
    return { success: false, error: errorMessage };
  }
}

// Function to make authenticated POST requests
export async function post<T>(path: string, data: any, contentType: string = "application/json"): Promise<ApiResponse<T>> {
  const token = getToken();
  const url = `${API_BASE_URL}${path}`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": contentType,
        ...(token && { "Authorization": `Bearer ${token}` }),
      },
      body: contentType === "application/x-www-form-urlencoded" ? new URLSearchParams(data).toString() : JSON.stringify(data),
    });

    if (!response.ok) {
      const errorText = await response.text();
      const errorMessage = errorText || response.statusText;
      toast.error(`API Error: ${errorMessage}`);
      return { success: false, error: errorMessage, status: response.status };
    }

    const responseData = await response.json();
    return { success: true, data: responseData.data };
  } catch (error: any) {
    const errorMessage = error.message || "Network error or API is unreachable.";
    toast.error(`API Error: ${errorMessage}`);
    return { success: false, error: errorMessage };
  }
}

// Add other HTTP methods (PUT, DELETE) as needed 