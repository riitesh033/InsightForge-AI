/**
 * Clear the application's shared authentication state.
 * @param {{ removeItem: (key: string) => void }} storage
 */
export function clearAuthSession(storage) {
  storage.removeItem("access_token");
  storage.removeItem("user");
}
