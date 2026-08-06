import { apiGet } from "./client";

export type VersionInfo = {
  application: string;
  version: string;
  api_version: string;
  demo_mode: boolean;
  git_commit: string | null;
  build_date: string | null;
};

export type RuntimeSettings = {
  ffprobe_path: string;
  ffprobe_timeout: number;
  scan_concurrency: number;
  scheduled_scan_enabled: boolean;
  scheduled_scan_interval_minutes: number;
  stale_retention_days: number;
  timezone: string;
};

export function getVersion(signal?: AbortSignal) {
  return apiGet<VersionInfo>("/api/v1/version", signal);
}

export function getRuntimeSettings(signal?: AbortSignal) {
  return apiGet<RuntimeSettings>("/api/v1/runtime-settings", signal);
}
