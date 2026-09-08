export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  full_name: string;
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  full_name: string;
  email: string;
  profile_picture?: string | null;
  is_active: boolean;
  is_superuser?: boolean;
  created_at?: string;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;

  login: (
    email: string,
    password: string
  ) => Promise<void>;

  register: (
    full_name: string,
    email: string,
    password: string
  ) => Promise<void>;

  logout: () => void;

  isAuthenticated: boolean;
}