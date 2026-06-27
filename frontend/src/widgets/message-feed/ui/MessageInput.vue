<script setup lang="ts">
import { computed, ref } from "vue";

const text = ref("");

const emit = defineEmits<{
  submit: [value: string];
}>();

const trimmedLength = computed(() => text.value.trim().length);

const onSubmit = () => {
  const trimmed = text.value.trim();
  if (!trimmed) return;
  emit("submit", trimmed);
  text.value = "";
};
</script>

<template>
  <form class="message-input card-surface" @submit.prevent="onSubmit">
    <label for="chat-message">Ваше сообщение</label>
    <textarea id="chat-message" v-model="text" rows="3" maxlength="512" placeholder="Введите сообщение..." />
    <div class="actions">
      <small>{{ trimmedLength }}/512</small>
      <button type="submit">Отправить</button>
    </div>
  </form>
</template>

<style scoped>
.message-input {
  display: grid;
  gap: 8px;
}

label {
  font-weight: 700;
}

textarea {
  resize: vertical;
  font-family: inherit;
  min-height: 90px;
}

.actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

small {
  color: var(--text-muted);
}
</style>
