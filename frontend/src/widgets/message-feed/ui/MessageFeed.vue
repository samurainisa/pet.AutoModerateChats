<script setup lang="ts">
import type { ChatMessage } from "@/entities/message";

import MessageInput from "./MessageInput.vue";
import MessageList from "./MessageList.vue";

defineProps<{
  items: ChatMessage[];
}>();

const emit = defineEmits<{
  submit: [text: string];
}>();
</script>

<template>
  <div class="message-feed">
    <MessageInput @submit="emit('submit', $event)" />
    <MessageList :items="items" />
  </div>
</template>

<style scoped>
.message-feed {
  display: grid;
  gap: 12px;
}
</style>
