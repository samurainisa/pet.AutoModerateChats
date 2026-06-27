import axios, { type AxiosInstance, type AxiosRequestConfig } from "axios";

class HttpClient {
  private static instance: HttpClient | null = null;
  private readonly client: AxiosInstance;

  private constructor() {
    this.client = axios.create({
      baseURL: "/api",
      withCredentials: true
    });
  }

  static getInstance(): HttpClient {
    HttpClient.instance ??= new HttpClient();
    return HttpClient.instance;
  }

  get axios(): AxiosInstance {
    return this.client;
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async patch<T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }
}

export const httpClient = HttpClient.getInstance();
