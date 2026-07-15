import {
  createContext,
  useEffect,
  useState,
  ReactNode,
} from "react";

import {
  LoginResponse,
  User,
  AuthContextType,
} from "@/types/auth";

import {
  saveToken,
  getToken,
  removeToken,
  saveUser,
  getUser,
  removeUser,
} from "@/utils/storage";

// Rename imported functions
import {
  login as loginService,
  register as registerService,
} from "@/services/auth";

export const AuthContext =
  createContext<AuthContextType>(
    {} as AuthContextType
  );

type Props = {
  children: ReactNode;
};

export function AuthProvider({
  children,
}: Props) {
  const [user, setUser] =
    useState<User | null>(null);

  const [token, setToken] =
    useState<string | null>(null);

  const [loading, setLoading] =
    useState(true);

  useEffect(() => {
    const storedToken = getToken();
    const storedUser = getUser<User>();

    if (storedToken) {
      setToken(storedToken);
    }

    if (storedUser) {
      setUser(storedUser);
    }

    setLoading(false);
  }, []);

  async function login(
    email: string,
    password: string
  ) {
    const response: LoginResponse =
      await loginService({
        email,
        password,
      });

    saveToken(response.access_token);
    setToken(response.access_token);
  }

  async function register(
    full_name: string,
    email: string,
    password: string
  ) {
    await registerService({
      full_name,
      email,
      password,
    });
  }

  function logout() {
    removeToken();
    removeUser();

    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}