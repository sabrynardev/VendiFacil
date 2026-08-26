import { api } from "./api";
import type { User } from "../types";

export async function login(email: string, password: string) {
  const { data } = await api.post<{ access_token: string }>("/auth/login", { email, password });
  return data;
}

export async function fetchMe() {
  const { data } = await api.get<User>("/auth/me");
  return data;
}
