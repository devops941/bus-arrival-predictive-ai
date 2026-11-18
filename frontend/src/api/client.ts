import type {
  AuthResponse,
  User,
  Route,
  Stop,
  Trip,
  Observation,
  DelayEvent,
  DelayTrendsSummary,
  HeatmapCell,
  RouteSummaryItem,
  EtaPredictionRequest,
  EtaPredictionResponse,
  AccuracyOverview,
  AccuracyByRoute,
  PredVsActualPoint,
  ErrorHistogramBin,
  AlertItem,
  ModelItem,
  TrainingJob,
  ImportValidationReport,
  FeaturePreview,
  ReportItem,
  AuditLogEntry,
  SystemDiagnostics,
} from '../types';

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api';

export interface ApiError {
  message: string;
  code?: string;
  fields?: Record<string, string>;
  status?: number;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  private getToken(): string | null {
    return localStorage.getItem('busarrival_access_token');
  }

  private getRefreshToken(): string | null {
    return localStorage.getItem('busarrival_refresh_token');
  }

  public setTokens(access: string, refresh: string) {
    localStorage.setItem('busarrival_access_token', access);
    localStorage.setItem('busarrival_refresh_token', refresh);
  }

  public clearTokens() {
    localStorage.removeItem('busarrival_access_token');
    localStorage.removeItem('busarrival_refresh_token');
    localStorage.removeItem('busarrival_user');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    isRetry = false
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    // Auto set Content-Type to JSON unless FormData
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const token = this.getToken();
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle 401 Unauthorized for token refresh
      if (response.status === 401 && !isRetry && !endpoint.includes('/auth/')) {
        const refreshed = await this.tryRefreshToken();
        if (refreshed) {
          return this.request<T>(endpoint, options, true);
        } else {
          this.clearTokens();
          window.dispatchEvent(new Event('auth:unauthorized'));
          throw {
            message: 'Session expired. Please log in again.',
            code: 'SESSION_EXPIRED',
            status: 401,
          } as ApiError;
        }
      }

      if (!response.ok) {
        let errData: any = {};
        try {
          errData = await response.json();
        } catch {
          errData = { detail: response.statusText };
        }

        const detailMsg = typeof errData.detail === 'string'
          ? errData.detail
          : errData.detail?.detail || errData.message || (errData.detail ? JSON.stringify(errData.detail) : 'An unexpected error occurred.');

        const apiError: ApiError = {
          message: String(detailMsg),
          code: errData.code || errData.detail?.code,
          fields: errData.fields,
          status: response.status,
        };
        throw apiError;
      }

      if (response.status === 204) {
        return {} as T;
      }

      return (await response.json()) as T;
    } catch (err: any) {
      if (err.status) throw err;
      throw {
        message: err.message || 'Network error. Please verify the backend is running.',
        code: 'NETWORK_ERROR',
      } as ApiError;
    }
  }

  private async tryRefreshToken(): Promise<boolean> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return false;

    try {
      const res = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!res.ok) return false;
      const data: AuthResponse = await res.json();
      this.setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  // ---------------- AUTH ----------------
  async login(formData: FormData | Record<string, any>): Promise<AuthResponse> {
    let payload: Record<string, any> = {};

    if (formData instanceof FormData) {
      formData.forEach((value, key) => { payload[key] = String(value); });
    } else {
      payload = { ...formData };
    }

    const res = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      const detailMsg = typeof err.detail === 'string' ? err.detail : err.detail?.detail;
      throw {
        message: detailMsg || 'Invalid email or password.',
        code: err.code || err.detail?.code || 'AUTH_FAILED',
        fields: err.fields,
        status: res.status,
      } as ApiError;
    }

    const data: any = await res.json();
    this.setTokens(data.access_token, data.refresh_token);
    const userObj = data.user || {
      id: data.user_id,
      email: data.email,
      full_name: data.full_name || '',
      role: data.role,
      is_active: true,
    };
    localStorage.setItem('busarrival_user', JSON.stringify(userObj));
    return {
      ...data,
      user: userObj,
    } as AuthResponse;
  }

  async register(payload: { email: string; password: string; full_name: string; role?: string }): Promise<AuthResponse> {
    return this.request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getMe(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  async logout(): Promise<void> {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } catch {
      // ignore
    } finally {
      this.clearTokens();
    }
  }

  // ---------------- ROUTES & STOPS ----------------
  async getRoutes(): Promise<Route[]> {
    return this.request<Route[]>('/routes');
  }

  async getRoute(routeId: string): Promise<Route> {
    return this.request<Route>(`/routes/${routeId}`);
  }

  async createRoute(data: Partial<Route>): Promise<Route> {
    return this.request<Route>('/routes', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateRoute(routeId: string, data: Partial<Route>): Promise<Route> {
    return this.request<Route>(`/routes/${routeId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteRoute(routeId: string): Promise<void> {
    return this.request<void>(`/routes/${routeId}`, { method: 'DELETE' });
  }

  async getStops(): Promise<Stop[]> {
    return this.request<Stop[]>('/stops');
  }

  async createStop(data: Partial<Stop>): Promise<Stop> {
    return this.request<Stop>('/stops', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateStop(stopId: string, data: Partial<Stop>): Promise<Stop> {
    return this.request<Stop>(`/stops/${stopId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteStop(stopId: string): Promise<void> {
    return this.request<void>(`/stops/${stopId}`, { method: 'DELETE' });
  }

  // ---------------- TRIPS & OBSERVATIONS ----------------
  async getTrips(routeId?: string): Promise<Trip[]> {
    const query = routeId ? `?route_id=${encodeURIComponent(routeId)}` : '';
    return this.request<Trip[]>(`/trips${query}`);
  }

  async createTrip(data: Partial<Trip>): Promise<Trip> {
    return this.request<Trip>('/trips', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getObservations(limit = 100): Promise<Observation[]> {
    return this.request<Observation[]>(`/observations?limit=${limit}`);
  }

  async createObservation(data: Partial<Observation>): Promise<Observation> {
    return this.request<Observation>('/observations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async deleteObservation(obsId: string): Promise<void> {
    return this.request<void>(`/observations/${obsId}`, { method: 'DELETE' });
  }

  async getDelayEvents(): Promise<DelayEvent[]> {
    return this.request<DelayEvent[]>('/delay-events');
  }

  async createDelayEvent(data: Partial<DelayEvent>): Promise<DelayEvent> {
    return this.request<DelayEvent>('/delay-events', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ---------------- CSV IMPORT ----------------
  async importDataset(
    kind: string,
    file: File,
    commit = false,
    importValidOnly = true
  ): Promise<ImportValidationReport> {
    const formData = new FormData();
    formData.append('file', file);
    const query = `?commit=${commit}&import_valid_only=${importValidOnly}`;
    return this.request<ImportValidationReport>(`/import/${kind}${query}`, {
      method: 'POST',
      body: formData,
    });
  }

  // ---------------- ANALYTICS ----------------
  async getDelayTrends(routeId?: string): Promise<DelayTrendsSummary> {
    const query = routeId ? `?route_id=${encodeURIComponent(routeId)}` : '';
    return this.request<DelayTrendsSummary>(`/analytics/delay-trends${query}`);
  }

  async getHeatmap(routeId?: string): Promise<{ cells: HeatmapCell[]; metadata?: any }> {
    const query = routeId ? `?route_id=${encodeURIComponent(routeId)}` : '';
    return this.request<{ cells: HeatmapCell[]; metadata?: any }>(`/analytics/heatmap${query}`);
  }

  async getRouteSummary(): Promise<RouteSummaryItem[]> {
    return this.request<RouteSummaryItem[]>('/analytics/route-summary');
  }

  // ---------------- FEATURES ----------------
  async buildFeatures(): Promise<any> {
    return this.request<any>('/features/build', { method: 'POST' });
  }

  async previewFeatures(): Promise<FeaturePreview> {
    return this.request<FeaturePreview>('/features/preview');
  }

  // ---------------- PREDICTIONS ----------------
  async predictEta(payload: EtaPredictionRequest): Promise<EtaPredictionResponse> {
    return this.request<EtaPredictionResponse>('/predict/eta', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getRouteCorridor(routeId: string): Promise<any> {
    return this.request<any>(`/predict/route/${routeId}`);
  }

  async triggerDriftCheck(): Promise<any> {
    return this.request<any>('/predict/drift-check', { method: 'POST' });
  }

  // ---------------- MODELS ----------------
  async getModels(): Promise<ModelItem[]> {
    return this.request<ModelItem[]>('/models');
  }

  async compareModels(): Promise<any[]> {
    return this.request<any[]>('/models/compare');
  }

  async trainModel(algorithm: string, randomSeed = 42): Promise<TrainingJob> {
    return this.request<TrainingJob>('/models/train', {
      method: 'POST',
      body: JSON.stringify({ algorithm, random_seed: randomSeed }),
    });
  }

  async getJobStatus(jobId: string): Promise<TrainingJob> {
    return this.request<TrainingJob>(`/models/jobs/${jobId}`);
  }

  async activateModel(modelId: string): Promise<any> {
    return this.request<any>(`/models/${modelId}/activate`, { method: 'POST' });
  }

  async rollbackModel(): Promise<any> {
    return this.request<any>('/models/rollback', { method: 'POST' });
  }

  // ---------------- ACCURACY ----------------
  async getAccuracyOverview(): Promise<AccuracyOverview> {
    return this.request<AccuracyOverview>('/accuracy/overview');
  }

  async getAccuracyErrors(): Promise<{ bins: ErrorHistogramBin[]; mean: number; std: number }> {
    return this.request<{ bins: ErrorHistogramBin[]; mean: number; std: number }>('/accuracy/errors');
  }

  async getAccuracyByRoute(): Promise<AccuracyByRoute[]> {
    return this.request<AccuracyByRoute[]>('/accuracy/by-route');
  }

  async getPredVsActual(): Promise<PredVsActualPoint[]> {
    return this.request<PredVsActualPoint[]>('/accuracy/predicted-vs-actual');
  }

  async getLeaveRouteOut(): Promise<any[]> {
    return this.request<any[]>('/accuracy/leave-route-out');
  }

  // ---------------- ALERTS ----------------
  async getAlerts(): Promise<AlertItem[]> {
    return this.request<AlertItem[]>('/alerts');
  }

  async resolveAlert(id: string): Promise<void> {
    return this.request<void>(`/alerts/${id}/resolve`, { method: 'POST' });
  }

  // ---------------- REPORTS ----------------
  async getReports(): Promise<ReportItem[]> {
    return this.request<ReportItem[]>('/reports');
  }

  async createReport(payload: { title: string; format: string; route_id?: string }): Promise<ReportItem> {
    return this.request<ReportItem>('/reports', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  getReportDownloadUrl(reportId: string): string {
    const token = this.getToken();
    return `${this.baseUrl}/reports/${reportId}/download${token ? `?token=${token}` : ''}`;
  }

  // ---------------- ADMIN ----------------
  async getAdminUsers(): Promise<any[]> {
    return this.request<any[]>('/admin/users');
  }

  async updateAdminUserRole(userId: string, role: string): Promise<any> {
    return this.request<any>(`/admin/users/${userId}/role`, {
      method: 'PUT',
      body: JSON.stringify({ role }),
    });
  }

  async updateAdminUserStatus(userId: string, isActive: boolean): Promise<any> {
    return this.request<any>(`/admin/users/${userId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ is_active: isActive }),
    });
  }

  async getAdminAuditLog(): Promise<AuditLogEntry[]> {
    return this.request<AuditLogEntry[]>('/admin/audit-log');
  }

  async getAdminSystemDiagnostics(): Promise<SystemDiagnostics> {
    return this.request<SystemDiagnostics>('/admin/system');
  }
}

export const api = new ApiClient(API_BASE_URL);
