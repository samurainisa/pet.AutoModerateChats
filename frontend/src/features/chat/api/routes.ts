export const CHAT_ROUTES = {
  messages: "/messages"
} as const;

export const CHAT_ROOM = "public" as const;

export const CHAT_SOCKET_EVENTS = {
  connect: "connect",
  disconnect: "disconnect",
  newMessage: "new_message",
  messageBlocked: "message_blocked",
  messageUpdated: "message_updated",
  messageHidden: "message_hidden",
  sendMessage: "send_message"
} as const;
