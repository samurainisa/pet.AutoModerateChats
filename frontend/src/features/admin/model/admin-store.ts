import { defineStore } from "pinia";

import type { AdminSettings, AdminStats, AdminUserListItem, AdminUserProfile, AdminUserUpdatePayload } from "@/entities/admin";

import { adminApi } from "../api/admin-api";

const DEFAULT_SETTINGS: AdminSettings = {
  low_threshold: 0.4,
  high_threshold: 0.75,
  flood_count: 5,
  flood_window: 30,
  duplicate_window: 30,
  temp_block_hours: 24
};

interface AdminState {
  stats: AdminStats | null;
  users: AdminUserListItem[];
  selectedUserProfile: AdminUserProfile | null;
  usersLoading: boolean;
  profileLoading: boolean;
  settingsDraft: AdminSettings;
}

export const useAdminStore = defineStore("admin", {
  state: (): AdminState => ({
    stats: null,
    users: [],
    selectedUserProfile: null,
    usersLoading: false,
    profileLoading: false,
    settingsDraft: { ...DEFAULT_SETTINGS }
  }),
  actions: {
    async loadStats() {
      this.stats = await adminApi.loadStats();
    },
    async loadUsers(query?: string) {
      this.usersLoading = true;
      try {
        const response = await adminApi.loadUsers(query);
        this.users = response.items ?? [];
      } finally {
        this.usersLoading = false;
      }
    },
    async loadUserProfile(userId: number) {
      this.profileLoading = true;
      try {
        this.selectedUserProfile = await adminApi.loadUserProfile(userId);
      } finally {
        this.profileLoading = false;
      }
    },
    clearSelectedUser() {
      this.selectedUserProfile = null;
    },
    async updateSettings() {
      await adminApi.updateSettings(this.settingsDraft);
    },
    async updateUser(userId: number, payload: AdminUserUpdatePayload) {
      const response = await adminApi.updateUser(userId, payload);
      const updated = response.user;

      const index = this.users.findIndex((item) => item.id === userId);
      if (index >= 0) {
        this.users[index] = { ...this.users[index], ...updated };
      }

      if (this.selectedUserProfile?.user.id === userId) {
        this.selectedUserProfile.user = {
          ...this.selectedUserProfile.user,
          ...updated
        };
      }
    }
  }
});
