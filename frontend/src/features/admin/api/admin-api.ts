import type {
  AdminSettings,
  AdminStats,
  AdminUserListItem,
  AdminUserProfile,
  AdminUserUpdatePayload
} from "@/entities/admin";
import { httpClient, type PaginatedResponse } from "@/shared/api";

import { ADMIN_ROUTES } from "./routes";

interface UpdateUserResponse {
  user: AdminUserListItem;
}

class AdminApi {
  loadStats(): Promise<AdminStats> {
    return httpClient.get<AdminStats>(ADMIN_ROUTES.stats);
  }

  loadUsers(query?: string): Promise<PaginatedResponse<AdminUserListItem>> {
    return httpClient.get<PaginatedResponse<AdminUserListItem>>(ADMIN_ROUTES.users, {
      params: query ? { q: query } : undefined
    });
  }

  loadUserProfile(userId: number): Promise<AdminUserProfile> {
    return httpClient.get<AdminUserProfile>(ADMIN_ROUTES.userProfile(userId));
  }

  updateSettings(settings: AdminSettings): Promise<void> {
    return httpClient.patch<void, AdminSettings>(ADMIN_ROUTES.settings, settings);
  }

  updateUser(userId: number, payload: AdminUserUpdatePayload): Promise<UpdateUserResponse> {
    return httpClient.patch<UpdateUserResponse, AdminUserUpdatePayload>(
      ADMIN_ROUTES.updateUser(userId),
      payload
    );
  }
}

export const adminApi = new AdminApi();
