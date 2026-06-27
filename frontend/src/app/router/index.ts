import { createRouter, createWebHistory } from "vue-router";

import AdminPage from "@/pages/admin/ui/AdminPage.vue";
import ChatPage from "@/pages/chat/ui/ChatPage.vue";
import LoginPage from "@/pages/login/ui/LoginPage.vue";
import ModerationPage from "@/pages/moderation/ui/ModerationPage.vue";
import RegisterPage from "@/pages/register/ui/RegisterPage.vue";

import { authGuard } from "./guards";
import { APP_ROUTES } from "./routes";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: APP_ROUTES.home, redirect: APP_ROUTES.chat },
    { path: APP_ROUTES.login, component: LoginPage, meta: { public: true } },
    { path: APP_ROUTES.register, component: RegisterPage, meta: { public: true } },
    { path: APP_ROUTES.chat, component: ChatPage },
    { path: APP_ROUTES.moderation, component: ModerationPage, meta: { role: "moderator" } },
    { path: APP_ROUTES.admin, component: AdminPage, meta: { role: "admin" } }
  ]
});

router.beforeEach(authGuard);

export default router;
