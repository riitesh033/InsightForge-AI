export function clearAuthSession(storage: {
  removeItem: (key: string) => void;
}): void;
