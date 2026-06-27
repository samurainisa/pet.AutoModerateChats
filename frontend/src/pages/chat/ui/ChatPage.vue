<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";

import { useChatStore } from "@/features/chat";
import { MessageFeed } from "@/widgets/message-feed";
import ToastMessage from "@/shared/ui/ToastMessage.vue";
import { codeLabel, formatDecisionReason, ruleLabel } from "@/shared/lib/locale";

const chatStore = useChatStore();

onMounted(async () => {
  chatStore.connect();
  await chatStore.loadHistory();
});

onUnmounted(() => {
  chatStore.clearNotices();
});

const onSubmit = (text: string) => {
  chatStore.sendMessage(text);
};
</script>

<template>
  <section class="chat-page">
    <section class="page-header card-surface">
      <h2>Публичный чат</h2>
      <p>Все сообщения проходят серверную модерацию до публикации.</p>
    </section>

    <div class="alerts">
      <ToastMessage
        v-if="chatStore.blockedNotice"
        title="Сообщение заблокировано"
        type="error"
        :text="`${formatDecisionReason(chatStore.blockedNotice.reason || codeLabel('blocked'))} (правило: ${ruleLabel(chatStore.blockedNotice.rule || 'n_a')})`"
      />
      <ToastMessage
        v-if="chatStore.hiddenNotice"
        title="Сообщение скрыто"
        type="warning"
        :text="`#${chatStore.hiddenNotice.id} оценка=${chatStore.hiddenNotice.score?.toFixed(3)} ${formatDecisionReason(chatStore.hiddenNotice.reason)}`"
      />
    </div>

    <MessageFeed :items="chatStore.messages" @submit="onSubmit" />
  </section>
</template>

<style scoped>
.chat-page {
  display: grid;
  gap: 12px;
}

.page-header h2 {
  margin: 0 0 6px;
}

.page-header p {
  margin: 0;
  color: var(--text-muted);
}

.alerts {
  display: grid;
  gap: 8px;
}
</style>
