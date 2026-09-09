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

export interface ForgotPasswordResponse {
  message: string;
  reset_token?: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface UserUpdate {
  full_name: string;
  email: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
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


/*
|--------------------------------------------------------------------------
| Forgot Password
|--------------------------------------------------------------------------
*/

export async function forgotPassword(
  email: string
): Promise<ForgotPasswordResponse> {

  const response =
    await api.post<ForgotPasswordResponse>(
      "/auth/forgot-password",
      {
        email: email.trim(),
      }
    );

  return response.data;
}


/*
|--------------------------------------------------------------------------
| Reset Password
|--------------------------------------------------------------------------
*/

export async function resetPassword(
  token: string,
  newPassword: string
): Promise<{ message: string }> {

  const response =
    await api.post<{ message: string }>(
      "/auth/reset-password",
      {
        token,
        new_password: newPassword,
      }
    );

  return response.data;
}


/*
|--------------------------------------------------------------------------
| Get Current User
|--------------------------------------------------------------------------
*/

export async function getCurrentUser(): Promise<{
  id: number;
  full_name: string;
  email: string;
  profile_picture?: string | null;
  is_active: boolean;
  is_superuser?: boolean;
  created_at?: string;
}> {

  const response =
    await api.get<{
      id: number;
      full_name: string;
      email: string;
      profile_picture?: string | null;
      is_active: boolean;
      is_superuser?: boolean;
      created_at?: string;
    }>("/users/me");

  return response.data;
}


/*
|--------------------------------------------------------------------------
| Update Profile
|--------------------------------------------------------------------------
*/

export async function updateProfile(
  full_name: string,
  email: string
): Promise<{
  id: number;
  full_name: string;
  email: string;
  profile_picture?: string | null;
  is_active: boolean;
}> {

  const response =
    await api.patch<{
      id: number;
      full_name: string;
      email: string;
      profile_picture?: string | null;
      is_active: boolean;
    }>(
      "/users/me",
      {
        full_name: full_name.trim(),
        email: email.trim(),
      }
    );

  return response.data;
}


/*
|--------------------------------------------------------------------------
| Change Password
|--------------------------------------------------------------------------
*/

export async function changePassword(
  currentPassword: string,
  newPassword: string
): Promise<{ message: string }> {

  const response =
    await api.post<{ message: string }>(
      "/users/me/change-password",
      {
        current_password: currentPassword,
        new_password: newPassword,
      }
    );

  return response.data;
}


/*
|--------------------------------------------------------------------------
| Upload Profile Picture
|--------------------------------------------------------------------------
*/

export async function uploadProfilePicture(
  file: File
): Promise<{
  id: number;
  full_name: string;
  email: string;
  profile_picture?: string | null;
  is_active: boolean;
}> {

  const formData = new FormData();
  formData.append("file", file);

  const response =
    await api.post<{
      id: number;
      full_name: string;
      email: string;
      profile_picture?: string | null;
      is_active: boolean;
    }>(
      "/users/me/profile-picture",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );

  return response.data;
}


/*
|--------------------------------------------------------------------------
| Set Built-in Avatar
|--------------------------------------------------------------------------
*/

export async function setBuiltinAvatar(
  avatarId: string
): Promise<{
  id: number;
  full_name: string;
  email: string;
  profile_picture?: string | null;
  is_active: boolean;
}> {

  const response =
    await api.post<{
      id: number;
      full_name: string;
      email: string;
      profile_picture?: string | null;
      is_active: boolean;
    }>(
      "/users/me/avatar",
      null,
      {
        params: {
          avatar_id: avatarId,
        },
      }
    );

  return response.data;
}


/*
|--------------------------------------------------------------------------
| Remove Profile Picture
|--------------------------------------------------------------------------
*/

export async function removeProfilePicture(): Promise<{
  id: number;
  full_name: string;
  email: string;
  profile_picture?: string | null;
  is_active: boolean;
}> {

  const response =
    await api.delete<{
      id: number;
      full_name: string;
      email: string;
      profile_picture?: string | null;
      is_active: boolean;
    }>("/users/me/profile-picture");

  return response.data;
}


/*
|--------------------------------------------------------------------------
| Delete Account
|--------------------------------------------------------------------------
*/

export async function deleteAccount(): Promise<void> {
  await api.delete("/users/me");
}