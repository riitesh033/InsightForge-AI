// Authentication Request Types

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  full_name: string;
  email: string;
  password: string;
}

// Authentication Response

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

// User Model

export interface User {
  id: number;
  full_name: string;
  email: string;
  is_active: boolean;
}

// Context State

export interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;

  login: (email: string, password: string) => Promise<void>;
  register: (
    full_name: string,
    email: string,
    password: string
  ) => Promise<void>;

  logout: () => void;

  isAuthenticated: boolean;
}