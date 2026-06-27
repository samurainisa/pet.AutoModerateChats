<script setup lang="ts">
import type { ChatMessage } from "@/entities/message";
import { statusLabel } from "@/shared/lib/locale";

defineProps<{
  message: ChatMessage;
}>();
</script>

<template>
  <article class="message-item card-surface">
    <div class="row">
      <strong>{{ message.author }}</strong>
      <time>{{ new Date(message.timestamp).toLocaleString("ru-RU") }}</time>
    </div>
    <p class="text">{{ message.text }}</p>
    <span class="status" :class="`status-${message.status}`">{{ statusLabel(message.status) }}</span>
  </article>
</template>

<style scoped>
.message-item {
  padding: 12px 14px;
  border-radius: 16px;
  display: grid;
  gap: 8px;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

time {
  color: var(--text-muted);
  font-size: 12px;
}

.text {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.4;
}

.status {
  width: fit-content;
  font-size: 11px;
  padding: 4px 9px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-weight: 700;
}

.status-ok,
.status-approved_manual {
  background: #e7f7ed;
  color: #1e7c46;
  border-color: #bbe6c9;
}

.status-hidden {
  background: #fff7e5;
  color: #916000;
  border-color: #efd9a6;
}

.status-blocked,
.status-deleted {
  background: #ffe9e8;
  color: #a22d35;
  border-color: #f6c4c8;
}
</style>
