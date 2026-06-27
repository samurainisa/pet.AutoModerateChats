import { defineStore } from "pinia";

import type {
  ChatMessage,
  MessageBlockedPayload,
  MessageHiddenPayload,
  MessageUpdatedPayload
} from "@/entities/message";

import { chatApi } from "../api/chat-api";
import { CHAT_ROOM, CHAT_SOCKET_EVENTS } from "../api/routes";
import { chatSocketClient } from "../api/chat-socket";

interface ChatState {
  messages: ChatMessage[];
  blockedNotice: MessageBlockedPayload | null;
  hiddenNotice: MessageHiddenPayload | null;
  socketReady: boolean;
  handlersBound: boolean;
}

export const useChatStore = defineStore("chat", {
  state: (): ChatState => ({
    messages: [],
    blockedNotice: null,
    hiddenNotice: null,
    socketReady: false,
    handlersBound: false
  }),
  actions: {
    bindSocketHandlers() {
      if (this.handlersBound) {
        return;
      }
      this.handlersBound = true;

      const socket = chatSocketClient.client;

      socket.on(CHAT_SOCKET_EVENTS.connect, () => {
        this.socketReady = true;
      });

      socket.on(CHAT_SOCKET_EVENTS.disconnect, () => {
        this.socketReady = false;
      });

      socket.on(CHAT_SOCKET_EVENTS.newMessage, (payload: ChatMessage) => {
        this.messages.unshift(payload);
      });

      socket.on(CHAT_SOCKET_EVENTS.messageBlocked, (payload: MessageBlockedPayload) => {
        this.blockedNotice = payload;
      });

      socket.on(CHAT_SOCKET_EVENTS.messageUpdated, (payload: MessageUpdatedPayload) => {
        const item = this.messages.find((message) => message.id === payload.id);
        if (item) {
          item.status = payload.status;
        }
      });

      socket.on(CHAT_SOCKET_EVENTS.messageHidden, (payload: MessageHiddenPayload) => {
        this.hiddenNotice = payload;
      });
    },
    connect() {
      this.bindSocketHandlers();
      chatSocketClient.connect();
    },
    disconnect() {
      chatSocketClient.disconnect();
    },
    async loadHistory() {
      const response = await chatApi.loadHistory();
      this.messages = response.items ?? [];
    },
    sendMessage(text: string) {
      chatSocketClient.sendMessage(CHAT_ROOM, text);
    },
    clearNotices() {
      this.blockedNotice = null;
      this.hiddenNotice = null;
    }
  }
});
