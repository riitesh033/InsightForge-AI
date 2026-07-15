import api from "./api";

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  full_name: string;
  email: string;
  password: string;
}

export async function login(data: LoginData) {
  const response = await api.post("/api/v1/auth/login", data);
  return response.data;
}

export async function register(data: RegisterData) {
  const response = await api.post("/api/v1/auth/register", data);
  return response.data;
}