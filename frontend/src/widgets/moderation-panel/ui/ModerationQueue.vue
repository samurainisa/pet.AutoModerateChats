<script setup lang="ts">
import type { HiddenQueueItem } from "@/entities/moderation";
import { formatDecisionReason, ruleLabel } from "@/shared/lib/locale";

defineProps<{
  items: HiddenQueueItem[];
}>();

const emit = defineEmits<{
  approve: [id: number];
  remove: [id: number];
  mute: [id: number];
  profile: [userId: number];
}>();
</script>

<template>
  <section class="queue card-surface">
    <div class="table-wrap">
      <table class="soft-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Автор</th>
            <th>Текст</th>
            <th>Оценка</th>
            <th>Причина</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>#{{ item.id }}</td>
            <td>{{ item.author }}</td>
            <td class="text-cell">{{ item.text }}</td>
            <td>{{ item.score?.toFixed(3) }}</td>
            <td>
              <div>{{ formatDecisionReason(item.reason) }}</div>
              <small class="meta" v-if="item.rule_triggered">Правило: {{ ruleLabel(item.rule_triggered) }}</small>
            </td>
            <td>
              <div class="actions">
                <button type="button" @click="emit('approve', item.id)">Одобрить</button>
                <button type="button" @click="emit('remove', item.id)">Удалить</button>
                <button type="button" class="btn-ghost" @click="emit('mute', item.id)">Мут 24ч</button>
                <button type="button" class="btn-link" @click="emit('profile', item.author_id)">Профиль</button>
              </div>
            </td>
          </tr>
          <tr v-if="items.length === 0">
            <td colspan="6" class="empty">Очередь скрытых сообщений пуста.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.table-wrap {
  overflow: auto;
  border-radius: 14px;
  border: 1px solid var(--border-soft);
}

.soft-table {
  width: 100%;
  min-width: 980px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.actions button {
  font-size: 12px;
  padding: 7px 10px;
}

.text-cell {
  max-width: 420px;
  white-space: normal;
  line-height: 1.35;
}

.meta {
  color: var(--text-muted);
}

.empty {
  color: var(--text-muted);
  text-align: center;
}
</style>
