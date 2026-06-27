<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";

import { APP_ROUTES } from "@/app/router/routes";
import { useAuthStore } from "@/features/auth";
import { roleLabel } from "@/shared/lib/locale";

const authStore = useAuthStore();
const router = useRouter();

const isModerator = computed(
  () => authStore.user?.role === "moderator" || authStore.user?.role === "admin"
);
const isAdmin = computed(() => authStore.user?.role === "admin");

onMounted(async () => {
  await authStore.fetchMe();
});

const onLogout = async () => {
  await authStore.logout();
  await router.push(APP_ROUTES.login);
};
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand">
        <span class="brand-dot" />
        <div class="brand-text">
          <strong>AutoModerate</strong>
          <small>Публичный чат</small>
        </div>
      </div>

      <nav class="nav">
        <router-link :to="APP_ROUTES.chat">Чат</router-link>
        <router-link v-if="isModerator" :to="APP_ROUTES.moderation">Модерация</router-link>
        <router-link v-if="isAdmin" :to="APP_ROUTES.admin">Админ-панель</router-link>
      </nav>

      <div class="auth-actions">
        <template v-if="authStore.user">
          <span class="user-pill">{{ authStore.user.username }} · {{ roleLabel(authStore.user.role) }}</span>
          <button type="button" class="btn-ghost" @click="onLogout">Выйти</button>
        </template>
        <template v-else>
          <router-link class="login-link" :to="APP_ROUTES.login">Войти</router-link>
        </template>
      </div>
    </header>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap");

:global(:root) {
  --bg-main: #f2f7fb;
  --bg-elevated: #ffffff;
  --bg-soft: #f8fbff;
  --text-primary: #1a2a45;
  --text-muted: #63708a;
  --accent: #2a78d0;
  --accent-strong: #165fb2;
  --border-soft: #dbe6f4;
  --shadow-soft: 0 12px 30px rgba(29, 72, 132, 0.08);
  --radius-xl: 22px;
  --radius-lg: 16px;
  --radius-md: 12px;
}

:global(*) {
  box-sizing: border-box;
}

:global(body) {
  margin: 0;
  min-height: 100vh;
  font-family: "Manrope", "Segoe UI", sans-serif;
  color: var(--text-primary);
  background:
    radial-gradient(circle at 0% 0%, rgba(95, 160, 255, 0.2) 0%, transparent 35%),
    radial-gradient(circle at 100% 10%, rgba(122, 205, 183, 0.18) 0%, transparent 30%),
    linear-gradient(180deg, #eff5fb 0%, #f7fbff 100%);
}

:global(input),
:global(select),
:global(textarea) {
  width: 100%;
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-md);
  padding: 10px 12px;
  font-size: 14px;
  background: #ffffff;
  color: var(--text-primary);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

:global(input:focus),
:global(select:focus),
:global(textarea:focus) {
  outline: none;
  border-color: #8bb9ec;
  box-shadow: 0 0 0 4px rgba(80, 141, 214, 0.16);
}

:global(button) {
  border: none;
  border-radius: 12px;
  background: linear-gradient(180deg, #3b89dd 0%, #2a6fc0 100%);
  color: #fff;
  padding: 9px 14px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.2s ease, background 0.2s ease;
}

:global(button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 8px 14px rgba(30, 87, 153, 0.25);
}

:global(button:disabled) {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

:global(a) {
  color: var(--accent-strong);
  text-decoration: none;
  font-weight: 600;
}

:global(a:hover) {
  color: #114e97;
}

:global(.card-surface) {
  background: var(--bg-elevated);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-xl);
  padding: 16px;
  box-shadow: var(--shadow-soft);
}

:global(.btn-link) {
  border: none;
  background: transparent;
  color: var(--accent-strong);
  padding: 0;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

:global(.btn-link:hover) {
  color: #114e97;
  text-decoration: underline;
}

:global(.btn-ghost) {
  background: #eef5ff;
  color: #1e5ea9;
  border: 1px solid #d4e4fa;
}

:global(.btn-ghost:hover) {
  background: #e6f0fd;
}

:global(.soft-table) {
  border-collapse: collapse;
}

:global(.soft-table th),
:global(.soft-table td) {
  text-align: left;
  padding: 11px 12px;
  border-bottom: 1px solid var(--border-soft);
  font-size: 13px;
}

:global(.soft-table thead th) {
  position: sticky;
  top: 0;
  background: #f5f9ff;
  z-index: 1;
  color: #1f3e6f;
}

.app-shell {
  min-height: 100vh;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 14px 18px;
  margin: 10px auto 0;
  width: min(1200px, calc(100vw - 20px));
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-xl);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  box-shadow: var(--shadow-soft);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: radial-gradient(circle at 25% 25%, #80c1ff 0%, #2a6fc0 80%);
  box-shadow: 0 0 0 4px rgba(64, 133, 215, 0.15);
}

.brand-text {
  display: grid;
  gap: 2px;
}

.brand-text strong {
  line-height: 1;
}

.brand-text small {
  color: var(--text-muted);
  line-height: 1;
}

.nav {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav a {
  padding: 8px 12px;
  border-radius: 999px;
  color: #245892;
}

.nav a.router-link-active {
  background: #e8f2ff;
  color: #154986;
}

.auth-actions {
  margin-left: auto;
  display: flex;
  gap: 10px;
  align-items: center;
}

.user-pill {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: 999px;
  background: #edf5ff;
  border: 1px solid #d3e3fb;
  color: #1f4f8c;
  font-size: 13px;
  font-weight: 700;
}

.login-link {
  padding: 8px 12px;
  border-radius: 999px;
  background: #eef5ff;
  border: 1px solid #d4e5fb;
}

.main-content {
  max-width: 1200px;
  margin: 16px auto 0;
  padding: 0 12px 24px;
}

@media (max-width: 860px) {
  .topbar {
    flex-wrap: wrap;
    gap: 12px;
    width: calc(100vw - 16px);
    margin-top: 8px;
  }

  .nav {
    order: 3;
    width: 100%;
    overflow-x: auto;
  }

  .auth-actions {
    margin-left: 0;
  }
}
</style>
