<script setup lang="ts">
import { reactive } from "vue";
import { useRouter } from "vue-router";

import { APP_ROUTES } from "@/app/router/routes";
import { useAuthStore } from "@/features/auth";
import { authErrorLabel } from "@/shared/lib/locale";

const router = useRouter();
const authStore = useAuthStore();

const form = reactive({
  username: "",
  password: ""
});

const onSubmit = async () => {
  try {
    await authStore.login(form);
    await router.push(APP_ROUTES.chat);
  } catch {
    // error stored in authStore
  }
};
</script>

<template>
  <section class="auth-page">
    <form class="auth-form card-surface" @submit.prevent="onSubmit">
      <h2>Вход</h2>
      <p>Введите данные аккаунта, чтобы открыть чат и модераторские функции.</p>

      <label>
        Имя пользователя
        <input v-model="form.username" required />
      </label>

      <label>
        Пароль
        <input v-model="form.password" type="password" required />
      </label>

      <button type="submit">Войти</button>

      <p v-if="authStore.error" class="error">{{ authErrorLabel(authStore.error) }}</p>
      <router-link class="sub-link" :to="APP_ROUTES.register">Создать аккаунт</router-link>
    </form>
  </section>
</template>

<style scoped>
.auth-page {
  max-width: 500px;
  margin: 48px auto;
}

.auth-form {
  display: grid;
  gap: 12px;
}

.auth-form h2 {
  margin: 0;
}

.auth-form p {
  margin: 0;
  color: var(--text-muted);
}

label {
  display: grid;
  gap: 6px;
}

.error {
  color: #a42432;
  font-weight: 700;
}

.sub-link {
  width: fit-content;
}
</style>
