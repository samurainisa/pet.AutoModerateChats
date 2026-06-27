import { defineStore } from "pinia";

import type { User } from "@/entities/user";
import { extractApiError } from "@/shared/api";

import { authApi } from "../api/auth-api";
import type { LoginPayload, RegisterPayload } from "./types";

interface AuthState {
  user: User | null;
  loaded: boolean;
  loading: boolean;
  error: string | null;
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    user: null,
    loaded: false,
    loading: false,
    error: null
  }),
  actions: {
    async fetchMe() {
      this.loading = true;
      try {
        const response = await authApi.fetchMe();
        this.user = response.user;
      } catch {
        this.user = null;
      } finally {
        this.loading = false;
        this.loaded = true;
      }
    },
    async register(payload: RegisterPayload) {
      this.error = null;
      try {
        const response = await authApi.register(payload);
        this.user = response.user;
      } catch (error: unknown) {
        this.error = extractApiError(error, "register_failed");
        throw error;
      }
    },
    async login(payload: LoginPayload) {
      this.error = null;
      try {
        const response = await authApi.login(payload);
        this.user = response.user;
      } catch (error: unknown) {
        this.error = extractApiError(error, "login_failed");
        throw error;
      }
    },
    async logout() {
      try {
        await authApi.logout();
      } catch {
        // session may already be expired
      } finally {
        this.user = null;
      }
    }
  }
});
