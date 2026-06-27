import type { ChatMessage } from "@/entities/message";
import { httpClient, type PaginatedResponse } from "@/shared/api";

import { CHAT_ROOM, CHAT_ROUTES } from "./routes";

class ChatApi {
  loadHistory(limit = 50): Promise<PaginatedResponse<ChatMessage>> {
    return httpClient.get<PaginatedResponse<ChatMessage>>(CHAT_ROUTES.messages, {
      params: { room: CHAT_ROOM, limit }
    });
  }
}

export const chatApi = new ChatApi();
