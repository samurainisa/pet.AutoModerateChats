<script setup lang="ts">
import { onMounted } from "vue";

import { useModerationStore } from "@/features/moderation";
import { ModerationPanel } from "@/widgets/moderation-panel";
import { violationLabel } from "@/shared/lib/locale";

const moderationStore = useModerationStore();

onMounted(async () => {
  await Promise.all([moderationStore.loadQueue(), moderationStore.loadViolations()]);
});

const onApprove = async (id: number) => {
  await moderationStore.approveMessage(id);
};

const onDelete = async (id: number) => {
  await moderationStore.deleteMessage(id);
};

const onMute = async (id: number) => {
  await moderationStore.muteUser(id, 24);
};

const onProfile = async (userId: number) => {
  await moderationStore.loadUserProfile(userId);
};
</script>

<template>
  <section class="moderation-page">
    <section class="page-header card-surface">
      <h2>Очередь модерации</h2>
      <p>Сообщения со статусом hidden требуют ручного решения модератора.</p>
    </section>

    <ModerationPanel
      :queue="moderationStore.queue"
      :profile="moderationStore.selectedProfile"
      @approve="onApprove"
      @remove="onDelete"
      @mute="onMute"
      @profile="onProfile"
    />

    <section class="violations card-surface">
      <h3>Последние нарушения</h3>
      <ul v-if="moderationStore.violations.length">
        <li v-for="item in moderationStore.violations" :key="item.id">
          {{ item.created_at }} | {{ item.username }} | {{ violationLabel(item.type) }} | оценка: {{ item.score }}
        </li>
      </ul>
      <p v-else class="muted">Нарушения не найдены.</p>
    </section>
  </section>
</template>

<style scoped>
.moderation-page {
  display: grid;
  gap: 14px;
}

.page-header h2 {
  margin: 0 0 6px;
}

.page-header p {
  margin: 0;
  color: var(--text-muted);
}

.violations ul {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 6px;
}

.muted {
  margin: 0;
  color: var(--text-muted);
}
</style>
