<script setup lang="ts">
import { computed, reactive, watch } from "vue";

import type { AdminUserProfile } from "@/entities/admin";
import { formatDecisionReason, roleLabel, statusLabel, violationLabel } from "@/shared/lib/locale";

const props = defineProps<{
  open: boolean;
  loading: boolean;
  profile: AdminUserProfile | null;
}>();

const emit = defineEmits<{
  close: [];
  save: [payload: { userId: number; data: Record<string, unknown> }];
}>();

const actionLabels: Record<string, string> = {
  approve: "Одобрено",
  delete: "Удалено",
  mute_user: "Пользователь заглушен",
  unmute_user: "Снят мут"
};

const form = reactive({
  role: "user",
  is_blocked: false,
  warnings: 0,
  rating_score: 0,
  shadow_ban: false
});

const statusBreakdown = computed(() => Object.entries(props.profile?.summary.status_breakdown || {}));

const formatDate = (value?: string | null) => {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ru-RU", { dateStyle: "short", timeStyle: "short" }).format(date);
};

const actionLabel = (value?: string | null) => {
  if (!value) return "-";
  return actionLabels[value] || value;
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

watch(
  () => props.profile?.user.id,
  () => {
    const user = props.profile?.user;
    if (!user) return;
    form.role = user.role;
    form.is_blocked = user.is_blocked;
    form.warnings = user.warnings;
    form.rating_score = Number(user.rating_score || 0);
    form.shadow_ban = user.shadow_ban;
  },
  { immediate: true }
);

const onSave = () => {
  if (!props.profile) return;
  emit("save", {
    userId: props.profile.user.id,
    data: {
      role: form.role,
      is_blocked: form.is_blocked,
      warnings: form.warnings,
      rating_score: form.rating_score,
      shadow_ban: form.shadow_ban
    }
  });
};
</script>

<template>
  <div v-if="open" class="modal-overlay" @click.self="emit('close')">
    <section class="modal-panel card-surface">
      <div class="modal-header">
        <div>
          <h3 v-if="profile">Профиль: {{ profile.user.username }}</h3>
          <h3 v-else>Профиль пользователя</h3>
          <p>Просмотр истории и настройка ограничений пользователя.</p>
        </div>
        <button type="button" class="btn-ghost" @click="emit('close')">Закрыть</button>
      </div>

      <p v-if="loading" class="muted">Загрузка профиля...</p>
      <p v-else-if="!profile" class="muted">Не удалось загрузить профиль пользователя.</p>

      <template v-else>
        <section class="overview-grid">
          <article class="surface">
            <h4>Основные данные</h4>
            <div class="meta-grid">
              <div>
                <span class="meta-key">ID</span>
                <strong>#{{ profile.user.id }}</strong>
              </div>
              <div>
                <span class="meta-key">Email</span>
                <strong>{{ profile.user.email || "не указан" }}</strong>
              </div>
              <div>
                <span class="meta-key">Роль</span>
                <strong>{{ roleLabel(profile.user.role) }}</strong>
              </div>
              <div>
                <span class="meta-key">Создан</span>
                <strong>{{ formatDate(profile.user.created_at || null) }}</strong>
              </div>
              <div>
                <span class="meta-key">Предупреждения</span>
                <strong>{{ profile.user.warnings }}</strong>
              </div>
              <div>
                <span class="meta-key">Рейтинг</span>
                <span :class="['status-badge', ratingTone(profile.user.rating_score)]">
                  {{ ratingText(profile.user.rating_score) }} · {{ profile.user.rating_score.toFixed(3) }}
                </span>
              </div>
            </div>
          </article>

          <article class="surface">
            <h4>Редактирование</h4>
            <form class="edit-form" @submit.prevent="onSave">
              <label>
                Роль
                <select v-model="form.role">
                  <option value="user">{{ roleLabel("user") }}</option>
                  <option value="moderator">{{ roleLabel("moderator") }}</option>
                  <option value="admin">{{ roleLabel("admin") }}</option>
                </select>
              </label>

              <label class="toggle">
                <span>Заблокирован</span>
                <input v-model="form.is_blocked" type="checkbox" />
              </label>

              <label class="toggle">
                <span>Теневой бан</span>
                <input v-model="form.shadow_ban" type="checkbox" />
              </label>

              <label>
                Предупреждения
                <input v-model.number="form.warnings" type="number" min="0" />
              </label>

              <label>
                Рейтинг
                <input v-model.number="form.rating_score" type="number" min="0" max="1" step="0.01" />
              </label>

              <button type="submit">Сохранить изменения</button>
            </form>
          </article>
        </section>

        <section class="surface">
          <h4>Сводка по активности</h4>
          <div class="summary-row">
            <div class="summary-pill">
              <span>Сообщений</span>
              <strong>{{ profile.summary.messages_total }}</strong>
            </div>
            <div class="summary-pill">
              <span>Нарушений</span>
              <strong>{{ profile.summary.violations_total }}</strong>
            </div>
          </div>
          <div class="status-line">
            <span v-for="[status, count] in statusBreakdown" :key="status" class="status-item">
              {{ statusLabel(status) }}: <strong>{{ count }}</strong>
            </span>
          </div>
        </section>

        <section class="surface">
          <h4>Последние сообщения</h4>
          <div class="table-wrap">
            <table class="soft-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Дата</th>
                  <th>Статус</th>
                  <th>Score</th>
                  <th>Причина</th>
                  <th>Текст</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="message in profile.messages" :key="message.id">
                  <td>#{{ message.id }}</td>
                  <td>{{ formatDate(message.created_at) }}</td>
                  <td>{{ statusLabel(message.status) }}</td>
                  <td>{{ message.score?.toFixed?.(3) ?? "-" }}</td>
                  <td>{{ formatDecisionReason(message.decision_reason) }}</td>
                  <td class="text-cell">{{ message.text }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="grid-2">
          <article class="surface">
            <h4>Последние нарушения</h4>
            <ul class="event-list" v-if="profile.violations.length">
              <li v-for="violation in profile.violations" :key="violation.id">
                <p>
                  <strong>{{ violationLabel(violation.type) }}</strong>
                  <span>сообщение #{{ violation.message_id }}</span>
                </p>
                <p>
                  Оценка: {{ violation.score ?? "-" }} | {{ formatDate(violation.created_at) }}
                </p>
              </li>
            </ul>
            <p v-else class="muted">Нарушения не найдены.</p>
          </article>

          <article class="surface">
            <h4>Действия модераторов</h4>
            <ul class="event-list" v-if="profile.moderation_actions.length">
              <li v-for="action in profile.moderation_actions" :key="action.id">
                <p>
                  <strong>{{ actionLabel(action.action) }}</strong>
                  <span>по сообщению #{{ action.message_id }}</span>
                </p>
                <p>
                  {{ action.moderator || "-" }} | {{ formatDate(action.created_at) }}
                </p>
              </li>
            </ul>
            <p v-else class="muted">Действий модераторов пока нет.</p>
          </article>
        </section>
      </template>
    </section>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: rgba(18, 30, 52, 0.38);
  backdrop-filter: blur(3px);
  display: grid;
  place-items: center;
  padding: 16px;
}

.modal-panel {
  width: min(1280px, 100%);
  max-height: calc(100vh - 32px);
  overflow: auto;
  display: grid;
  gap: 14px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 12px;
}

.modal-header h3 {
  margin: 0 0 6px;
}

.modal-header p {
  margin: 0;
  color: var(--text-muted);
}

.surface {
  border-radius: 14px;
  border: 1px solid var(--border-soft);
  background: #f9fcff;
  padding: 12px;
}

.overview-grid {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 12px;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 10px;
}

.meta-grid > div {
  display: grid;
  gap: 4px;
  padding: 10px;
  border-radius: 10px;
  border: 1px solid var(--border-soft);
  background: #fff;
}

.meta-key {
  color: var(--text-muted);
  font-size: 12px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 700;
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

.edit-form {
  display: grid;
  gap: 10px;
}

.toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid var(--border-soft);
  border-radius: 10px;
  background: #fff;
  padding: 9px 12px;
}

.toggle input[type="checkbox"] {
  width: 18px;
  height: 18px;
  margin: 0;
  flex: 0 0 auto;
}

.summary-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.summary-pill {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  border-radius: 999px;
  padding: 6px 12px;
  background: #edf5ff;
  color: #173f7f;
  border: 1px solid #d4e3ff;
}

.status-line {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.status-item {
  border-radius: 999px;
  padding: 5px 10px;
  background: #f7f9fc;
  border: 1px solid var(--border-soft);
}

.table-wrap {
  overflow: auto;
  border-radius: 12px;
  border: 1px solid var(--border-soft);
}

.soft-table {
  width: 100%;
  min-width: 880px;
}

.text-cell {
  max-width: 460px;
  white-space: normal;
  line-height: 1.35;
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.event-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 8px;
}

.event-list li {
  padding: 10px;
  border-radius: 10px;
  border: 1px solid var(--border-soft);
  background: #fff;
}

.event-list p {
  margin: 0;
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.event-list p + p {
  margin-top: 6px;
  color: var(--text-muted);
}

.muted {
  margin: 0;
  color: var(--text-muted);
}

@media (max-width: 1100px) {
  .overview-grid,
  .grid-2 {
    grid-template-columns: 1fr;
  }

  .modal-header {
    flex-direction: column;
  }
}
</style>
