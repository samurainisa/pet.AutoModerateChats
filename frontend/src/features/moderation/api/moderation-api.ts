import type { HiddenQueueItem, UserProfile, ViolationItem } from "@/entities/moderation";
import { httpClient, type PaginatedResponse } from "@/shared/api";

import { MODERATION_ROUTES } from "./routes";

class ModerationApi {
  loadQueue(): Promise<PaginatedResponse<HiddenQueueItem>> {
    return httpClient.get<PaginatedResponse<HiddenQueueItem>>(MODERATION_ROUTES.queue);
  }

  approveMessage(messageId: number): Promise<void> {
    return httpClient.post<void>(MODERATION_ROUTES.approveMessage(messageId));
  }

  deleteMessage(messageId: number): Promise<void> {
    return httpClient.post<void>(MODERATION_ROUTES.deleteMessage(messageId));
  }

  muteUser(messageId: number, hours: number): Promise<void> {
    return httpClient.post<void, { hours: number }>(MODERATION_ROUTES.muteUser(messageId), { hours });
  }

  loadUserProfile(userId: number): Promise<UserProfile> {
    return httpClient.get<UserProfile>(MODERATION_ROUTES.userProfile(userId));
  }

  loadViolations(): Promise<PaginatedResponse<ViolationItem>> {
    return httpClient.get<PaginatedResponse<ViolationItem>>(MODERATION_ROUTES.violations);
  }
}

export const moderationApi = new ModerationApi();
