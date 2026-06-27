import type { User } from "@/entities/user";

export interface HiddenQueueItem {
  id: number;
  text: string;
  author: string;
  author_id: number;
  score: number;
  reason: string;
  rule_triggered?: string | null;
  timestamp: string;
}

export interface ViolationItem {
  id: number;
  user_id: number;
  username: string;
  message_id: number;
  type: string;
  score: number;
  details_json: string;
  created_at: string;
}

export interface UserProfile {
  user: User;
  messages: Array<{
    id: number;
    text: string;
    status: string;
    score: number;
    created_at: string;
  }>;
  violations: Array<{
    id: number;
    type: string;
    score: number;
    details_json: string;
    created_at: string;
  }>;
}
