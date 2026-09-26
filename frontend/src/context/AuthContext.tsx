import {
  createContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import type {
  AuthContextType,
  User,
} from "@/types/auth";

import {
  getToken as getStoredToken,
  getUser as getStoredUser,
  saveToken,
  saveUser,
  clearAuthStorage,
} from "@/utils/storage";

import {
  login as loginService,
  register as registerService,
} from "@/services/auth";

import api from "@/lib/api";


export const AuthContext =
  createContext<AuthContextType | undefined>(undefined);


interface AuthProviderProps {
  children: ReactNode;
}


export function AuthProvider({
  children,
}: AuthProviderProps) {

  const [user, setUser] = useState<User | null>(null);

  const [token, setToken] = useState<string | null>(
    getStoredToken()
  );

  const [loading, setLoading] = useState(true);


  /*
   * Fetch the currently authenticated user
   * from the backend.
   */
  async function fetchCurrentUser(): Promise<User> {
    try {
      const response = await api.get<User>(
        "/users/me"
      );

      const currentUser = response.data;

      setUser(currentUser);
      saveUser(currentUser);

      return currentUser;

    } catch (error) {
      clearAuthStorage();

      setUser(null);
      setToken(null);

      throw error;
    }
  }


  /*
   * Restore authentication when the application starts.
   */
  useEffect(() => {

    async function restoreSession() {

      const storedToken = getStoredToken();
      const storedUser = getStoredUser<User>();

      if (!storedToken) {
        clearAuthStorage();
        setUser(null);
        setToken(null);
        setLoading(false);
        return;
      }


      setToken(storedToken);


      /*
       * Show stored user immediately if available.
       */
      if (storedUser) {
        setUser(storedUser);
      }


      /*
       * Verify token with backend.
       */
      try {
        await fetchCurrentUser();
      } catch {
        // Session has already been cleared.
      }


      setLoading(false);
    }


    restoreSession();

  }, []);


  /*
   * Login
   */
  async function login(
    email: string,
    password: string
  ): Promise<void> {

    const response = await loginService(
      email,
      password
    );

    const accessToken =
      response.access_token;


    /*
     * Save token.
     */
    saveToken(accessToken);
    setToken(accessToken);



    /*
     * Get the real user from backend.
     */
    try {
      const currentUser =
        await fetchCurrentUser();

      setUser(currentUser);

    } catch (error) {

      /*
       * If token is valid but /users/me fails,
       * remove the authentication state.
       */
      clearAuthStorage();

      setUser(null);
      setToken(null);

      throw error;
    }
  }


  /*
   * Register
   */
  async function register(
    full_name: string,
    email: string,
    password: string
  ): Promise<void> {

    await registerService(
      full_name,
      email,
      password
    );


    /*
     * Automatically login after registration.
     */
    await login(
      email,
      password
    );
  }


  /*
   * Logout - calls backend if needed and clears local state
   */
  async function logout(): Promise<void> {
    clearAuthStorage();

    setUser(null);
    setToken(null);
  }


  /*
   * Update user profile in context
   */
  function updateUserProfile(updatedUser: User): void {
    setUser(updatedUser);
    saveUser(updatedUser);
  }


  /*
   * Authentication state.
   */
  const isAuthenticated =
    Boolean(token && user);


  /*
   * Context value.
   */
  const contextValue: AuthContextType = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated,
    updateUserProfile,
  };


  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}