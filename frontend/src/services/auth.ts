import api from "@/lib/axios";
import { LoginRequest, RegisterRequest } from "@/types/auth";

export async function login(data: LoginRequest) {
  const response = await api.post("/auth/login", data);
  return response.data;
}

export async function register(data: RegisterRequest) {
  const response = await api.post("/auth/register", data);
  return response.data;
}