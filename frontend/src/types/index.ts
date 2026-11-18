export type Role = 'passenger' | 'analyst' | 'admin';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RouteStop {
  stop_id: string;
  stop_code?: string;
  sequence: number;
  distance_from_origin_km: number;
  scheduled_travel_min: number;
  scheduled_offset_min?: number;
}

export interface Route {
  id: string;
  route_no: string;
  name: string;
  origin: string;
  destination: string;
  total_distance_km: number;
  stops_count: number;
  color_hex?: string;
  status: 'active' | 'suspended';
  stops: RouteStop[];
}

export interface Stop {
  id: string;
  stop_code: string;
  name: string;
  lat?: number;
  lon?: number;
  latitude?: number;
  longitude?: number;
  is_active?: boolean;
}

export interface Trip {
  id: string;
  trip_id?: string;
  route_id?: string;
  route_no?: string;
  trip_number?: string;
  direction?: 'inbound' | 'outbound' | string;
  scheduled_start?: string;
  scheduled_end?: string;
  date?: string;
  vehicle_id?: string;
  day_type?: 'weekday' | 'weekend' | 'holiday' | string;
}

export interface Observation {
  id: string;
  trip_id: string;
  stop_id?: string;
  stop_code?: string;
  route_id?: string;
  route_no?: string;
  scheduled_arrival: string;
  actual_arrival: string;
  delay_min: number;
  precipitation_mm?: number;
  passenger_load_pct?: number;
  passengers_boarded?: number;
  passengers_alighted?: number;
  dwell_time_sec?: number;
  congestion_level?: string;
  weather_condition?: string;
}

export interface DelayEvent {
  id: string;
  route_id?: string;
  route_no?: string;
  stop_id?: string;
  date?: string;
  time?: string;
  start_time?: string;
  end_time?: string;
  cause?: string;
  minutes?: number;
  incident_type?: 'congestion' | 'breakdown' | 'weather' | 'accident' | 'signal_failure' | string;
  severity?: 'minor' | 'major' | 'critical' | string;
  impact_minutes?: number;
  notes?: string;
}

export interface DelayTrendsSummary {
  overall_on_time_pct: number;
  avg_delay_minutes: number;
  total_observations: number;
  minor_delay_pct: number;
  major_delay_pct: number;
  by_hour: Array<{
    hour: number;
    avg_delay: number;
    count: number;
    on_time_pct: number;
  }>;
  by_day_type: Array<{
    day_type: string;
    avg_delay: number;
    count: number;
    on_time_pct: number;
  }>;
}

export interface HeatmapCell {
  weekday: number; // 0=Monday, 6=Sunday
  weekday_name: string;
  hour: number;
  avg_delay: number;
  observation_count: number;
  congestion_level: 'low' | 'moderate' | 'high' | 'severe';
}

export interface RouteSummaryItem {
  route_id: string;
  route_no: string;
  route_name: string;
  trip_count: number;
  avg_delay: number;
  on_time_pct: number;
  major_delays_count: number;
}

export interface EtaPredictionRequest {
  route_id: string;
  stop_id: string;
  scheduled_arrival: string;
  precipitation_mm?: number;
  recent_corridor_delay?: number;
}

export interface CorridorStopPrediction {
  stop_id: string;
  stop_name: string;
  sequence: number;
  distance_from_origin_km: number;
  scheduled_time: string;
  predicted_eta_p50: string;
  predicted_eta_p90: string;
  predicted_delay_min: number;
  status: 'departed' | 'current' | 'upcoming';
}

export interface EtaPredictionResponse {
  prediction_id: string;
  route_id: string;
  stop_id: string;
  stop_name: string;
  scheduled_arrival: string;
  predicted_arrival_p50: string;
  predicted_arrival_p90: string;
  expected_delay_min: number;
  delay_range_min: {
    p50: number;
    p90: number;
  };
  reliability_tier: 'HIGH' | 'MEDIUM' | 'LOW';
  confidence_score: number;
  model_id: string;
  corridor_predictions?: CorridorStopPrediction[];
  disclaimer: string;
}

export interface AccuracyOverview {
  active_model_id: string;
  active_model_name: string;
  mae: number;
  rmse: number;
  within_2_min_pct: number;
  p90_coverage_pct: number;
  bias: number;
  sample_size: number;
  last_evaluated: string;
}

export interface AccuracyByRoute {
  route_id: string;
  route_no: string;
  route_name: string;
  mae: number;
  rmse: number;
  within_2_min_pct: number;
  sample_count: number;
}

export interface PredVsActualPoint {
  actual: number;
  predicted: number;
  route_id: string;
  route_no?: string;
  trip_id?: string;
  residual: number;
}

export interface ErrorHistogramBin {
  bin_center: number;
  bin_label: string;
  count: number;
  density: number;
}

export interface AlertItem {
  id: string;
  route_id?: string;
  model_id?: string;
  alert_type: 'accuracy_drift' | 'consecutive_delays' | 'data_anomaly';
  severity: 'low' | 'medium' | 'high';
  message: string;
  details: Record<string, any>;
  is_resolved: boolean;
  created_at: string;
}

export interface ModelItem {
  id: string;
  name: string;
  algorithm: string;
  status: 'candidate' | 'active' | 'archived';
  metrics: {
    mae: number;
    rmse: number;
    mape: number;
    within_2_min_pct: number;
    bias: number;
  };
  feature_importances?: Record<string, number>;
  created_at: string;
}

export interface TrainingJob {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  model_id?: string;
  error?: string;
}

export interface ImportIssueItem {
  row: number;
  field: string;
  issue_type: string;
  message: string;
  is_fatal: boolean;
}

export interface ImportValidationReport {
  kind: string;
  total_rows: number;
  valid_count: number;
  invalid_count: number;
  committed: boolean;
  issues: ImportIssueItem[];
}

export interface FeaturePreview {
  columns: string[];
  total_rows: number;
  sample: Record<string, any>[];
  statistics: Record<string, { mean: number; std: number; min: number; max: number }>;
}

export interface ReportItem {
  id: string;
  report_id?: string;
  title: string;
  format?: 'pdf' | 'xlsx' | 'csv' | 'html' | string;
  file_format?: string;
  date_range?: string;
  created_by?: string;
  created_at: string;
  file_size_kb?: number;
  row_count?: number;
  status?: string;
}

export interface AuditLogEntry {
  id: string;
  user_email: string;
  action: string;
  entity: string;
  entity_id?: string;
  timestamp: string;
  details?: Record<string, any>;
}

export interface SystemDiagnostics {
  status: string;
  db_status: string;
  collections: Record<string, number>;
  memory_usage?: string;
  uptime_seconds?: number;
}
