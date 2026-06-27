import type { User } from "@/entities/user";

export interface AdminStats {
  period: string;
  messages_total: number;
  messages_ok: number;
  messages_hidden: number;
  messages_blocked: number;
  top_violators: Array<{
    user_id: number;
    username: string;
    violations: number;
  }>;
}

export interface AdminUserListItem extends User {
  email?: string | null;
  created_at?: string | null;
  messages_total: number;
  violations_total: number;
}

export interface AdminUserProfile {
  user: AdminUserListItem;
  summary: {
    messages_total: number;
    violations_total: number;
    status_breakdown: Record<string, number>;
  };
  messages: Array<{
    id: number;
    text: string;
    status: string;
    score: number | null;
    rule_triggered: string | null;
    decision_reason: string | null;
    created_at: string | null;
  }>;
  violations: Array<{
    id: number;
    type: string;
    score: number | null;
    message_id: number;
    details_json: string | null;
    created_at: string | null;
  }>;
  moderation_actions: Array<{
    id: number;
    message_id: number;
    action: string;
    comment: string | null;
    moderator: string | null;
    created_at: string | null;
  }>;
}

export interface AdminSettings {
  low_threshold: number;
  high_threshold: number;
  flood_count: number;
  flood_window: number;
  duplicate_window: number;
  temp_block_hours: number;
}

export interface AdminUserUpdatePayload {
  role?: User["role"];
  is_blocked?: boolean;
  warnings?: number;
  rating_score?: number;
  shadow_ban?: boolean;
}
