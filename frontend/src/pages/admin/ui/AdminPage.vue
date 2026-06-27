<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { AdminSettings } from "@/entities/admin";
import { useAdminStore } from "@/features/admin";
import { AdminSettings as AdminSettingsForm, AdminUserModal } from "@/widgets/admin-panel";
import ToastMessage from "@/shared/ui/ToastMessage.vue";
import { roleLabel } from "@/shared/lib/locale";

const adminStore = useAdminStore();

const userSearch = ref("");
const modalOpen = ref(false);
const toastCounter = ref(0);
const toasts = ref<Array<{ id: number; title: string; text: string; type: "info" | "warning" | "error" }>>([]);

const topViolators = computed(() => adminStore.stats?.top_violators ?? []);

const pushToast = (title: string, text: string, type: "info" | "warning" | "error" = "info") => {
  const id = ++toastCounter.value;
  toasts.value.push({ id, title, text, type });
  window.setTimeout(() => {
    toasts.value = toasts.value.filter((item) => item.id !== id);
  }, 4200);
};

const dismissToast = (id: number) => {
  toasts.value = toasts.value.filter((item) => item.id !== id);
};

const ratingTone = (score: number) => {
  if (score >= 0.8) return "rating-critical";
  if (score >= 0.6) return "rating-high";
  if (score >= 0.4) return "rating-medium";
  return "rating-low";
};

const ratingText = (score: number) => {
  if (score >= 0.8) return "Критичный";
  if (score >= 0.6) return "Высокий";
  if (score >= 0.4) return "Средний";
  return "Низкий";
};

onMounted(async () => {
  try {
    await Promise.all([adminStore.loadStats(), adminStore.loadUsers()]);
  } catch {
    pushToast("Ошибка загрузки", "Не удалось загрузить данные админ-панели.", "error");
  }
});

const onSaveSettings = async (payload: AdminSettings) => {
  try {
    adminStore.settingsDraft = payload;
    await adminStore.updateSettings();
    await adminStore.loadStats();
    pushToast("Настройки сохранены", "Параметры модерации успешно обновлены.", "info");
  } catch {
    pushToast("Ошибка", "Не удалось сохранить настройки.", "error");
  }
};

const refreshAll = async () => {
  try {
    await Promise.all([adminStore.loadStats(), adminStore.loadUsers(userSearch.value.trim())]);
    pushToast("Данные обновлены", "Список пользователей и статистика актуализированы.", "info");
  } catch {
    pushToast("Ошибка", "Не удалось обновить данные.", "error");
  }
};

const onSearchUsers = async () => {
  try {
    await adminStore.loadUsers(userSearch.value.trim());
  } catch {
    pushToast("Ошибка поиска", "Не удалось выполнить поиск пользователей.", "error");
  }
};

const openUser = async (userId: number) => {
  modalOpen.value = true;
  adminStore.clearSelectedUser();
  try {
    await adminStore.loadUserProfile(userId);
  } catch {
    pushToast("Ошибка профиля", "Профиль пользователя не удалось загрузить.", "error");
    modalOpen.value = false;
  }
};

const closeModal = () => {
  modalOpen.value = false;
  adminStore.clearSelectedUser();
};

const onSaveUser = async (payload: { userId: number; data: Record<string, unknown> }) => {
  try {
    await adminStore.updateUser(payload.userId, payload.data);
    await Promise.all([adminStore.loadUserProfile(payload.userId), adminStore.loadUsers(userSearch.value.trim())]);
    pushToast("Пользователь обновлен", "Изменения профиля успешно сохранены.", "info");
  } catch {
    pushToast("Ошибка сохранения", "Не удалось обновить пользователя.", "error");
  }
};
</script>

<template>
  <section class="admin-page">
    <section class="page-header card-surface">
      <div>
        <h2>Панель администратора</h2>
        <p>Управляйте параметрами модерации и пользователями системы.</p>
      </div>
      <button type="button" class="btn-ghost" @click="refreshAll">Обновить данные</button>
    </section>

    <AdminSettingsForm :initial="adminStore.settingsDraft" @save="onSaveSettings" />

    <section class="stats card-surface" v-if="adminStore.stats">
      <h3>Статистика за 24 часа</h3>
      <div class="cards">
        <article class="stat-card">
          <span class="label">Всего сообщений</span>
          <strong>{{ adminStore.stats.messages_total }}</strong>
        </article>
        <article class="stat-card">
          <span class="label">Опубликовано</span>
          <strong>{{ adminStore.stats.messages_ok }}</strong>
        </article>
        <article class="stat-card">
          <span class="label">Скрыто</span>
          <strong>{{ adminStore.stats.messages_hidden }}</strong>
        </article>
        <article class="stat-card">
          <span class="label">Заблокировано</span>
          <strong>{{ adminStore.stats.messages_blocked }}</strong>
        </article>
      </div>

      <h4>Пользователи с наибольшим числом нарушений</h4>
      <ul class="violators-list" v-if="topViolators.length">
        <li v-for="item in topViolators" :key="item.user_id">
          <button type="button" class="btn-link" @click="openUser(item.user_id)">
            #{{ item.user_id }} {{ item.username }}
          </button>
          <span>{{ item.violations }} нарушений</span>
        </li>
      </ul>
      <p v-else class="muted">Нарушений за выбранный период не зафиксировано.</p>
    </section>

    <section class="users card-surface">
      <div class="users-head">
        <h3>Пользователи</h3>
        <form class="search-form" @submit.prevent="onSearchUsers">
          <input
            v-model="userSearch"
            type="search"
            placeholder="Поиск по имени пользователя"
            aria-label="Поиск пользователя"
          />
          <button type="submit">Найти</button>
        </form>
      </div>

      <div class="table-wrap">
        <table class="soft-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Пользователь</th>
              <th>Роль</th>
              <th>Рейтинг</th>
              <th>Предупреждения</th>
              <th>Сообщения</th>
              <th>Нарушения</th>
              <th>Статус</th>
              <th>Профиль</th>
            </tr>
          </thead>
          <tbody v-if="adminStore.users.length">
            <tr v-for="user in adminStore.users" :key="user.id" class="clickable-row" @click="openUser(user.id)">
              <td>#{{ user.id }}</td>
              <td class="user-name">{{ user.username }}</td>
              <td>{{ roleLabel(user.role) }}</td>
              <td>
                <span :class="['status-badge', ratingTone(user.rating_score)]">
                  {{ ratingText(user.rating_score) }} · {{ user.rating_score.toFixed(3) }}
                </span>
              </td>
              <td>{{ user.warnings }}</td>
              <td>{{ user.messages_total }}</td>
              <td>{{ user.violations_total }}</td>
              <td>
                <span :class="['status-badge', user.is_blocked ? 'blocked' : 'active']">
                  {{ user.is_blocked ? "Заблокирован" : "Активен" }}
                </span>
              </td>
              <td>
                <button type="button" class="btn-link" @click.stop="openUser(user.id)">Открыть</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-if="adminStore.usersLoading" class="muted">Загрузка пользователей...</p>
      <p v-else-if="!adminStore.users.length" class="muted">Пользователи не найдены.</p>
    </section>

    <AdminUserModal
      :open="modalOpen"
      :loading="adminStore.profileLoading"
      :profile="adminStore.selectedUserProfile"
      @close="closeModal"
      @save="onSaveUser"
    />

    <aside class="toast-stack">
      <div v-for="toast in toasts" :key="toast.id" class="toast-item">
        <ToastMessage :title="toast.title" :text="toast.text" :type="toast.type" />
        <button type="button" class="toast-close btn-ghost" @click="dismissToast(toast.id)">×</button>
      </div>
    </aside>
  </section>
</template>

<style scoped>
.admin-page {
  display: grid;
  gap: 18px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 16px;
}

.page-header h2 {
  margin: 0 0 6px;
}

.page-header p {
  margin: 0;
  color: var(--text-muted);
}

.cards {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.stat-card {
  display: grid;
  gap: 6px;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid var(--border-soft);
  background: linear-gradient(160deg, #f7fbff 0%, #f0f7ff 100%);
}

.stat-card .label {
  color: var(--text-muted);
  font-size: 13px;
}

.stat-card strong {
  font-size: 24px;
  color: var(--text-primary);
}

.violators-list {
  margin: 8px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 8px;
}

.violators-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.users-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.users-head h3 {
  margin: 0;
}

.search-form {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.table-wrap {
  overflow: auto;
  border-radius: 14px;
  border: 1px solid var(--border-soft);
}

.soft-table {
  width: 100%;
  min-width: 940px;
}

.clickable-row {
  cursor: pointer;
}

.user-name {
  font-weight: 600;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 700;
}

.status-badge.active {
  background: #e5f7ee;
  color: #17653c;
}

.status-badge.blocked {
  background: #ffe9e7;
  color: #a33532;
}

.status-badge.rating-low {
  background: #e5f7ee;
  color: #17653c;
}

.status-badge.rating-medium {
  background: #e8f1ff;
  color: #27579f;
}

.status-badge.rating-high {
  background: #fff3dd;
  color: #946000;
}

.status-badge.rating-critical {
  background: #ffe7e5;
  color: #a33532;
}

.muted {
  color: var(--text-muted);
  margin: 10px 0 0;
}

.toast-stack {
  position: fixed;
  top: 86px;
  right: 16px;
  z-index: 70;
  width: min(380px, calc(100vw - 32px));
  display: grid;
  gap: 10px;
}

.toast-item {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  align-items: start;
}

.toast-close {
  min-width: 34px;
  padding: 6px 8px;
}

@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
  }

  .users-head {
    flex-direction: column;
    align-items: stretch;
  }

  .toast-stack {
    top: auto;
    bottom: 14px;
    right: 12px;
    width: calc(100vw - 24px);
  }
}
</style>
