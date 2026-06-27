export const ADMIN_ROUTES = {
  stats: "/admin/stats",
  users: "/admin/users",
  settings: "/admin/settings",
  userProfile: (userId: number) => `/admin/users/${userId}`,
  updateUser: (userId: number) => `/admin/users/${userId}`
} as const;
