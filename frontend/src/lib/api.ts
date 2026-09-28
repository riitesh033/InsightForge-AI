import axios from "axios";
import { clearAuthStorage, getToken } from "@/utils/storage";

const configuredApiBaseUrl = import.meta.env.VITE_API_URL
  ?.trim()
  .replace(/^VITE_API_URL\s*=\s*/i, "");
const configuredBaseUrl =
  configuredApiBaseUrl ||
  (import.meta.env.DEV
    ? "http://localhost:8000/api/v1"
    : "/api/v1");

function withApiVersion(baseUrl: string): string {
  if (/^https?:\/\//i.test(baseUrl)) {
    const url = new URL(baseUrl);
    const path = url.pathname.replace(/\/+$/, "");
    url.pathname = /(?:^|\/)api\/v1$/i.test(path)
      ? path
      : `${path}/api/v1`;
    return url.toString().replace(/\/+$/, "");
  }

  const path = baseUrl.replace(/\/+$/, "");
  return /(?:^|\/)api\/v1$/i.test(path) ? path : `${path}/api/v1`;
}

const apiBaseUrl = withApiVersion(configuredBaseUrl);

const api = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    Accept: "application/json",
  },
  timeout: 120000,
});

api.interceptors.request.use(
  (config) => {
    const token = getToken();

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const requestUrl = error.config?.url ?? "";
      const isAuthenticationRequest =
        requestUrl.startsWith("/auth/login") ||
        requestUrl.startsWith("/auth/register") ||
        requestUrl.startsWith("/auth/forgot-password") ||
        requestUrl.startsWith("/auth/reset-password");
      const hadToken = getToken() !== null;

      if (!isAuthenticationRequest) {
        clearAuthStorage();

        if (hadToken && window.location.pathname !== "/login") {
          window.location.replace("/login");
        }
      }
    }

    return Promise.reject(error);
  }
);

export function getApiAssetUrl(path: string): string {
  return new URL(path, new URL(apiBaseUrl, window.location.origin)).toString();
}

export function getApiErrorMessage(
  error: unknown,
  fallback: string
): string {
  const details = getApiErrorDetails(error);
  if (typeof details.detail === "string") {
    return details.detail;
  }
  if (typeof details.message === "string") {
    return details.message;
  }

  return error instanceof Error ? error.message : fallback;
}

export interface ApiErrorDetails {
  status?: number;
  detail?: unknown;
  message?: unknown;
}

export function getApiErrorDetails(
  error: unknown
): ApiErrorDetails {
  if (axios.isAxiosError(error)) {
    const responseData = error.response?.data as
      | { detail?: unknown; message?: unknown }
      | undefined;

    return {
      status: error.response?.status,
      detail: responseData?.detail,
      message: responseData?.message,
    };
  }

  return {};
}

export default api;