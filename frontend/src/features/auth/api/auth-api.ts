import { httpClient } from "@/shared/api";
import type { AuthResponse, LoginPayload, RegisterPayload } from "../model/types";
import { AUTH_ROUTES } from "./routes";

class AuthApi {
  fetchMe(): Promise<AuthResponse> {
    return httpClient.get<AuthResponse>(AUTH_ROUTES.me);
  }

  register(payload: RegisterPayload): Promise<AuthResponse> {
    return httpClient.post<AuthResponse, RegisterPayload>(AUTH_ROUTES.register, payload);
  }

  login(payload: LoginPayload): Promise<AuthResponse> {
    return httpClient.post<AuthResponse, LoginPayload>(AUTH_ROUTES.login, payload);
  }

  logout(): Promise<void> {
    return httpClient.post<void>(AUTH_ROUTES.logout);
  }
}

export const authApi = new AuthApi();
