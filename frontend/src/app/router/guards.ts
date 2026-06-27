import type { NavigationGuard } from "vue-router";

import { useAuthStore } from "@/features/auth";
import type { AppRouteMeta } from "./routes";
import { APP_ROUTES, ROLE_WEIGHT } from "./routes";

export const authGuard: NavigationGuard = async (to) => {
  const authStore = useAuthStore();
  const meta = to.meta as AppRouteMeta;

  if (!authStore.loaded) {
    await authStore.fetchMe();
  }

  if (meta.public) {
    return true;
  }

  if (!authStore.user) {
    return APP_ROUTES.login;
  }

  const requiredRole = meta.role;
  if (requiredRole && ROLE_WEIGHT[authStore.user.role] < ROLE_WEIGHT[requiredRole]) {
    return APP_ROUTES.chat;
  }

  return true;
};
