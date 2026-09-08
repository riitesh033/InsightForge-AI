import api from "@/services/api";

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterResponse {
  id: number;
  full_name: string;
  email: string;
  is_active: boolean;
}


/*
|--------------------------------------------------------------------------
| Login
|--------------------------------------------------------------------------
*/

export async function login(
  email: string,
  password: string
): Promise<LoginResponse> {

  const formData = new URLSearchParams();

  formData.append("username", email.trim());
  formData.append("password", password);

  const response =
    await api.post<LoginResponse>(
      "/auth/login",
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


/*
|--------------------------------------------------------------------------
| Register
|--------------------------------------------------------------------------
*/

export async function register(
  full_name: string,
  email: string,
  password: string
): Promise<RegisterResponse> {

  const response =
    await api.post<RegisterResponse>(
      "/auth/register",
      {
        full_name: full_name.trim(),
        email: email.trim(),
        password,
      }
    );

  return response.data;
}