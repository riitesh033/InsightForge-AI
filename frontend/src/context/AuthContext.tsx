import {
  createContext,
  ReactNode,
  useEffect,
  useState,
} from "react";

import api from "@/services/api";

import {
  login as loginService,
  register as registerService,
} from "@/services/auth";

import {
  AuthContextType,
  LoginResponse,
  User,
} from "@/types/auth";

import {
  clearAuthStorage,
  getToken,
  getUser,
  saveToken,
  saveUser,
} from "@/utils/storage";

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

      api.defaults.headers.common.Authorization =
        `Bearer ${storedToken}`;
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

    api.defaults.headers.common.Authorization =
      `Bearer ${response.access_token}`;

    /*
      Later we will fetch the current user
      from the backend.

      For now we only store the email.
    */

    const currentUser: User = {
      id: 0,
      full_name: "",
      email,
      is_active: true,
    };

    saveUser(currentUser);

    setUser(currentUser);
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
    clearAuthStorage();

    delete api.defaults.headers.common.Authorization;

    setUser(null);
    setToken(null);
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