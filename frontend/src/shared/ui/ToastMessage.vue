<script setup lang="ts">
defineProps<{
  title: string;
  text: string;
  type?: "info" | "warning" | "error";
}>();
</script>

<template>
  <div class="toast" :class="`type-${type || 'info'}`">
    <strong>{{ title }}</strong>
    <p>{{ text }}</p>
  </div>
</template>

<style scoped>
.toast {
  border-radius: 10px;
  padding: 10px 12px;
  border: 1px solid;
}

.toast p {
  margin: 6px 0 0 0;
}

.type-info {
  background: #ecf5ff;
  border-color: #c5defa;
  color: #224f8f;
}

.type-warning {
  background: #fff8e6;
  border-color: #f4dfae;
  color: #8a5f00;
}

.type-error {
  background: #ffeaea;
  border-color: #f4bdbd;
  color: #921818;
}
</style>
