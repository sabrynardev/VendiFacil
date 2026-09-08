import { api } from "./api";
import type { User } from "../types";

export interface RegisterAccountPayload {
  account_name: string;
  admin_name: string;
  admin_email: string;
  password: string;
  with_default_categories: boolean;
}

export async function login(email: string, password: string) {
  const { data } = await api.post<{ access_token: string }>("/auth/login", { email, password });
  return data;
}

export async function fetchMe() {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

export async function registerAccount(payload: RegisterAccountPayload) {
  const { data } = await api.post<{ access_token: string }>("/accounts/register", payload);
  return data;
}
