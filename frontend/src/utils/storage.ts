//
// Authentication Storage Utilities
//

// =========================
// Storage Keys
// =========================

const ACCESS_TOKEN_KEY = "access_token";
const USER_KEY = "user";


// =========================
// Token
// =========================

/**
 * Save authentication access token.
 */
export function saveToken(token: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

/**
 * Get authentication access token.
 */
export function getToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Compatibility alias.
 *
 * Some parts of the application may use getStoredToken().
 */
export function getStoredToken(): string | null {
  return getToken();
}

/**
 * Remove authentication access token.
 */
export function removeToken(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
}


// =========================
// User
// =========================

/**
 * Save authenticated user information.
 */
export function saveUser<T>(user: T): void {
  localStorage.setItem(
    USER_KEY,
    JSON.stringify(user)
  );
}

/**
 * Get authenticated user information.
 */
export function getUser<T>(): T | null {
  const storedUser = localStorage.getItem(USER_KEY);

  if (!storedUser) {
    return null;
  }

  try {
    return JSON.parse(storedUser) as T;
  } catch (error) {
    console.error(
      "Failed to parse stored user:",
      error
    );

    // Remove corrupted user data.
    localStorage.removeItem(USER_KEY);

    return null;
  }
}

/**
 * Remove stored user information.
 */
export function removeUser(): void {
  localStorage.removeItem(USER_KEY);
}


// =========================
// Authentication Storage
// =========================

/**
 * Clear all authentication-related data.
 */
export function clearAuthStorage(): void {
  removeToken();
  removeUser();
}


// =========================
// Authentication Helpers
// =========================

/**
 * Check whether an access token exists.
 */
export function isAuthenticated(): boolean {
  return getToken() !== null;
}
