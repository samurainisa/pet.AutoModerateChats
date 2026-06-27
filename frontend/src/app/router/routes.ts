import type { UserRole } from "@/entities/user";

export const APP_ROUTES = {
  home: "/",
  chat: "/chat",
  login: "/login",
  register: "/register",
  moderation: "/moderation",
  admin: "/admin"
} as const;

export interface AppRouteMeta {
  public?: boolean;
  role?: UserRole;
}

export const ROLE_WEIGHT: Record<UserRole, number> = {
  user: 1,
  moderator: 2,
  admin: 3
};
