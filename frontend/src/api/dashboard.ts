import { apiGet } from "./client";

export type DashboardStats = {
  total_movies: number;
  total_episodes: number;
  total_media_files: number;
  scanned_files: number;
  files_with_czech_audio: number;
  files_missing_czech_audio: number;
  scan_errors: number;
  files_without_mappings: number;
  ignored_items: number;
  stale_items: number;
  last_synchronization_time: string | null;
  last_completed_scan_time: string | null;
  current_scan: {
    scan_run_id: number;
    status: string;
    completed_item_count: number;
    requested_item_count: number;
    current_status: string | null;
  } | null;
};

export function getDashboardStats(signal?: AbortSignal) {
  return apiGet<DashboardStats>("/api/v1/dashboard", signal);
}
