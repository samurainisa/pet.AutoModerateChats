import { io, type Socket } from "socket.io-client";

import { apiOrigin } from "@/shared/config/env";

import { CHAT_SOCKET_EVENTS } from "./routes";

class ChatSocketClient {
  private static instance: ChatSocketClient | null = null;
  private readonly socket: Socket;

  private constructor() {
    this.socket = io(`${apiOrigin}/chat`, {
      path: "/socket.io",
      withCredentials: true,
      autoConnect: false,
      transports: ["websocket"]
    });
  }

  static getInstance(): ChatSocketClient {
    ChatSocketClient.instance ??= new ChatSocketClient();
    return ChatSocketClient.instance;
  }

  get client(): Socket {
    return this.socket;
  }

  connect(): void {
    if (!this.socket.connected) {
      this.socket.connect();
    }
  }

  disconnect(): void {
    if (this.socket.connected) {
      this.socket.disconnect();
    }
  }

  sendMessage(room: string, text: string): void {
    this.socket.emit(CHAT_SOCKET_EVENTS.sendMessage, { room, text });
  }
}

export const chatSocketClient = ChatSocketClient.getInstance();
