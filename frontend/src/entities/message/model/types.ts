export type MessageStatus = "pending" | "ok" | "hidden" | "blocked" | "deleted" | "approved_manual";

export interface ChatMessage {
  id: number;
  author: string;
  text: string;
  timestamp: string;
  status: MessageStatus;
  score?: number | null;
}

export interface MessageBlockedPayload {
  reason?: string;
  score?: number;
  rule?: string;
}

export interface MessageHiddenPayload {
  id: number;
  reason: string;
  score: number;
}

export interface MessageUpdatedPayload {
  id: number;
  status: MessageStatus;
}
