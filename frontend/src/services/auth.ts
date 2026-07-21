import api from "./api";

// =========================
// Interfaces
// =========================

export interface RegisterData {
  full_name: string;
  email: string;
  password: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface ForgotPasswordData {
  email: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

// =========================
// Register
// =========================

export async function register(
  data: RegisterData
): Promise<any> {
  const response = await api.post(
    "/api/v1/auth/register",
    data
  );

  return response.data;
}

// =========================
// Login
// =========================

export async function login(
  data: LoginData
): Promise<LoginResponse> {
  const formData = new URLSearchParams();

  formData.append("username", data.email);
  formData.append("password", data.password);

  const response = await api.post(
    "/api/v1/auth/login",
    formData,
    {
      headers: {
        "Content-Type":
          "application/x-www-form-urlencoded",
      },
    }
  );

  return response.data;
}

// =========================
// Forgot Password
// =========================

export async function forgotPassword(
  data: ForgotPasswordData
): Promise<any> {
  const response = await api.post(
    "/api/v1/auth/forgot-password",
    data
  );

  return response.data;
}