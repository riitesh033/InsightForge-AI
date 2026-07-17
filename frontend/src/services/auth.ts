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

export async function register(data: RegisterData) {
  const response = await api.post(
    "/api/v1/auth/register",
    data
  );

  return response.data;
}

export async function login(data: LoginData) {
  const form = new URLSearchParams();

  form.append("username", data.email);
  form.append("password", data.password);

  const response = await api.post(
    "/api/v1/auth/login",
    form,
    {
      headers: {
        "Content-Type":
          "application/x-www-form-urlencoded",
      },
    }
  );

  return response.data;
}