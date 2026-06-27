import type { User } from "@/entities/user";

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  password: string;
  email?: string;
}

export interface AuthResponse {
  user: User;
}
