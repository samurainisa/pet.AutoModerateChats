import { defineStore } from "pinia";

import type { HiddenQueueItem, UserProfile, ViolationItem } from "@/entities/moderation";

import { moderationApi } from "../api/moderation-api";

interface ModerationState {
  queue: HiddenQueueItem[];
  violations: ViolationItem[];
  selectedProfile: UserProfile | null;
  loading: boolean;
}

export const useModerationStore = defineStore("moderation", {
  state: (): ModerationState => ({
    queue: [],
    violations: [],
    selectedProfile: null,
    loading: false
  }),
  actions: {
    async loadQueue() {
      this.loading = true;
      try {
        const response = await moderationApi.loadQueue();
        this.queue = response.items ?? [];
      } finally {
        this.loading = false;
      }
    },
    async approveMessage(messageId: number) {
      await moderationApi.approveMessage(messageId);
      await this.loadQueue();
    },
    async deleteMessage(messageId: number) {
      await moderationApi.deleteMessage(messageId);
      await this.loadQueue();
    },
    async muteUser(messageId: number, hours = 24) {
      await moderationApi.muteUser(messageId, hours);
    },
    async loadUserProfile(userId: number) {
      this.selectedProfile = await moderationApi.loadUserProfile(userId);
    },
    async loadViolations() {
      const response = await moderationApi.loadViolations();
      this.violations = response.items ?? [];
    }
  }
});
