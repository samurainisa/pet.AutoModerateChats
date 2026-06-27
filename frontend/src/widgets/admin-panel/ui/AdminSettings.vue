<script setup lang="ts">
import { reactive, watch } from "vue";

import type { AdminSettings } from "@/entities/admin";

const props = defineProps<{
  initial: AdminSettings;
}>();

const emit = defineEmits<{
  save: [payload: AdminSettings];
}>();

const form = reactive({ ...props.initial });

watch(
  () => props.initial,
  (value) => {
    Object.assign(form, value);
  }
);

const onSubmit = () => {
  emit("save", { ...form });
};
</script>

<template>
  <form class="settings-form card-surface" @submit.prevent="onSubmit">
    <div class="title-wrap">
      <h3>Системные настройки модерации</h3>
      <p>Изменения применяются к следующим входящим сообщениям.</p>
    </div>

    <div class="settings-grid">
      <label>
        Нижний порог (LOW)
        <input v-model.number="form.low_threshold" type="number" step="0.01" min="0" max="1" />
      </label>

      <label>
        Верхний порог (HIGH)
        <input v-model.number="form.high_threshold" type="number" step="0.01" min="0" max="1" />
      </label>

      <label>
        Лимит сообщений для flood
        <input v-model.number="form.flood_count" type="number" min="1" />
      </label>

      <label>
        Flood-окно (сек)
        <input v-model.number="form.flood_window" type="number" min="1" />
      </label>

      <label>
        Окно duplicate (сек)
        <input v-model.number="form.duplicate_window" type="number" min="1" />
      </label>

      <label>
        Временная блокировка (часы)
        <input v-model.number="form.temp_block_hours" type="number" min="1" />
      </label>
    </div>

    <div class="actions">
      <button type="submit">Сохранить настройки</button>
    </div>
  </form>
</template>

<style scoped>
.settings-form {
  display: grid;
  gap: 14px;
}

.title-wrap h3 {
  margin: 0 0 6px;
}

.title-wrap p {
  margin: 0;
  color: var(--text-muted);
}

.settings-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

label {
  display: grid;
  gap: 6px;
  font-size: 14px;
  color: var(--text-primary);
}

.actions {
  display: flex;
  justify-content: flex-end;
}
</style>
