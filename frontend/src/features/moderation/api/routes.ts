export const MODERATION_ROUTES = {
  queue: "/moderation/queue",
  violations: "/moderation/violations",
  approveMessage: (messageId: number) => `/moderation/messages/${messageId}/approve`,
  deleteMessage: (messageId: number) => `/moderation/messages/${messageId}/delete`,
  muteUser: (messageId: number) => `/moderation/messages/${messageId}/mute_user`,
  userProfile: (userId: number) => `/moderation/users/${userId}`
} as const;
