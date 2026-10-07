import axios from "axios";
import { clearAuthStorage, getToken } from "@/utils/storage";

const configuredApiBaseUrl = import.meta.env.VITE_API_URL
  ?.trim()
  .replace(/^VITE_API_URL\s*=\s*/i, "");
const defaultProductionApiBaseUrl =
  "https://insightforge-backend-5f1o.onrender.com/api/v1";
const configuredBaseUrl =
  configuredApiBaseUrl ||
  (import.meta.env.DEV
    ? "http://localhost:8000/api/v1"
    : defaultProductionApiBaseUrl);

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

export const API_BASE_URL = withApiVersion(configuredBaseUrl);

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    Accept: "application/json",
  },
  timeout: 120000,
});

api.interceptors.request.use(
  (config) => {
    const token = getToken();
    const authorization = config.headers.get("Authorization");

    if (token && !authorization) {
      config.headers.set("Authorization", `Bearer ${token}`);
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
      const requestAuthorization =
        error.config?.headers.get("Authorization");
      const currentToken = getToken();
      const isCurrentSessionRequest =
        typeof requestAuthorization === "string" &&
        currentToken !== null &&
        requestAuthorization === `Bearer ${currentToken}`;

      if (!isAuthenticationRequest && isCurrentSessionRequest) {
        clearAuthStorage();

        if (window.location.pathname !== "/login") {
          window.location.replace("/login");
        }
      }
    }

    return Promise.reject(error);
  }
);

export function getApiAssetUrl(path: string): string {
  return new URL(path, new URL(API_BASE_URL, window.location.origin)).toString();
}

export function getApiErrorMessage(
  error: unknown,
  fallback: string
): string {
  const details = getApiErrorDetails(error);
  if (typeof details.detail === "string") {
    return details.detail;
  }
  if (
    details.detail !== null &&
    typeof details.detail === "object" &&
    "message" in details.detail &&
    typeof details.detail.message === "string"
  ) {
    return details.detail.message;
  }
  if (typeof details.message === "string") {
    return details.message;
  }

  if (axios.isAxiosError(error) && error.response) {
    const responseData = error.response.data;
    if (typeof responseData === "string" && responseData.trim()) {
      try {
        const parsed = JSON.parse(responseData) as {
          detail?: unknown;
          message?: unknown;
        };
        if (typeof parsed.detail === "string") {
          return parsed.detail;
        }
        if (typeof parsed.message === "string") {
          return parsed.message;
        }
      } catch {
        return responseData;
      }
    }

    return `Request failed with status code ${error.response.status}`;
  }

  return error instanceof Error ? error.message : fallback;
}

export function isPlanRestrictionError(error: unknown): boolean {
  const detail = getApiErrorDetails(error).detail;
  if (detail === null || typeof detail !== "object" || !("code" in detail)) {
    return false;
  }

  return (
    detail.code === "PLAN_FEATURE_REQUIRED" ||
    detail.code === "PLAN_LIMIT_REACHED" ||
    detail.code === "AI_QUERY_LIMIT_REACHED"
  );
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