<script setup lang="ts">
import type { HiddenQueueItem, UserProfile as UserProfileData } from "@/entities/moderation";

import ModerationQueue from "./ModerationQueue.vue";
import UserProfileCard from "./UserProfile.vue";

defineProps<{
  queue: HiddenQueueItem[];
  profile: UserProfileData | null;
}>();

const emit = defineEmits<{
  approve: [id: number];
  remove: [id: number];
  mute: [id: number];
  profile: [userId: number];
}>();
</script>

<template>
  <div class="moderation-panel">
    <ModerationQueue
      :items="queue"
      @approve="emit('approve', $event)"
      @remove="emit('remove', $event)"
      @mute="emit('mute', $event)"
      @profile="emit('profile', $event)"
    />
    <UserProfileCard :profile="profile" />
  </div>
</template>

<style scoped>
.moderation-panel {
  display: grid;
  gap: 14px;
}
</style>
