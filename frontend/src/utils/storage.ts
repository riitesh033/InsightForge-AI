// Storage Keys

const ACCESS_TOKEN_KEY = "access_token";
const USER_KEY = "user";

// =========================
// Access Token
// =========================

export function saveToken(token: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function getToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function removeToken(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
}

// =========================
// User
// =========================

export function saveUser(user: unknown): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getUser<T>(): T | null {
  const user = localStorage.getItem(USER_KEY);

  if (!user) return null;

  return JSON.parse(user) as T;
}

export function removeUser(): void {
  localStorage.removeItem(USER_KEY);
}

// =========================
// Clear All Auth Data
// =========================

export function clearAuthStorage(): void {
  removeToken();
  removeUser();
}