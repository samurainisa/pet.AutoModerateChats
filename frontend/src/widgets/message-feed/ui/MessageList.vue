<script setup lang="ts">
import type { ChatMessage } from "@/entities/message";

import MessageItem from "./MessageItem.vue";

defineProps<{
  items: ChatMessage[];
}>();
</script>

<template>
  <section class="message-list">
    <MessageItem v-for="item in items" :key="item.id" :message="item" />
  </section>
</template>

<style scoped>
.message-list {
  display: grid;
  gap: 10px;
}
</style>
