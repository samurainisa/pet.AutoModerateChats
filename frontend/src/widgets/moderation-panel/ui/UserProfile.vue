<script setup lang="ts">
import type { UserProfile } from "@/entities/moderation";
import { roleLabel, statusLabel, violationLabel } from "@/shared/lib/locale";

defineProps<{
  profile: UserProfile | null;
}>();
</script>

<template>
  <section class="profile card-surface" v-if="profile">
    <h3>Профиль пользователя: {{ profile.user.username }}</h3>
    <div class="top-meta">
      <span>Роль: <strong>{{ roleLabel(profile.user.role) }}</strong></span>
      <span>Рейтинг: <strong>{{ profile.user.rating_score.toFixed(3) }}</strong></span>
      <span>Предупреждения: <strong>{{ profile.user.warnings }}</strong></span>
    </div>

    <div class="grid">
      <article>
        <h4>Последние сообщения</h4>
        <ul>
          <li v-for="msg in profile.messages" :key="msg.id">
            <p>#{{ msg.id }} · {{ statusLabel(msg.status) }} · score: {{ msg.score ?? "—" }}</p>
            <p>{{ msg.text }}</p>
            <p class="reason">{{ msg.created_at }}</p>
          </li>
        </ul>
      </article>

      <article>
        <h4>Нарушения</h4>
        <ul>
          <li v-for="violation in profile.violations" :key="violation.id">
            <p>{{ violationLabel(violation.type) }} · score: {{ violation.score ?? "—" }}</p>
            <p class="reason">{{ violation.created_at }}</p>
          </li>
        </ul>
      </article>
    </div>
  </section>
</template>

<style scoped>
.profile {
  display: grid;
  gap: 12px;
}

h3,
h4 {
  margin: 0;
}

.top-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.top-meta span {
  padding: 6px 10px;
  border-radius: 999px;
  background: #f1f7ff;
  border: 1px solid var(--border-soft);
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

ul {
  margin: 8px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 8px;
}

li {
  border-radius: 12px;
  border: 1px solid var(--border-soft);
  background: #f8fbff;
  padding: 10px;
}

li p {
  margin: 0;
  line-height: 1.35;
}

li p + p {
  margin-top: 6px;
}

.reason {
  color: var(--text-muted);
}

@media (max-width: 1024px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
