export type UserRole = "user" | "moderator" | "admin";

export interface User {
  id: number;
  username: string;
  role: UserRole;
  rating_score: number;
  warnings: number;
  is_blocked: boolean;
  blocked_until?: string | null;
  shadow_ban: boolean;
}
