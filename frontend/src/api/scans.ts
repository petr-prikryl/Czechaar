import { apiGet, apiRequest } from "./client";

export type ScanRun = {
  id: number;
  scan_type: string;
  source_type: string | null;
  integration_id: number | null;
  status: string;
  requested_item_count: number;
  completed_item_count: number;
  success_count: number;
  missing_czech_count: number;
  cache_hit_count: number;
  error_count: number;
  cancellation_requested: boolean;
  current_status: string | null;
  error_summary: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
};

export function startMediaFileScan(mediaFileId: number, force = true) {
  return apiRequest<ScanRun>("/api/v1/scans", {
    method: "POST",
    body: { scan_type: "media_file", media_file_id: mediaFileId, force },
  });
}

export function startSeriesScan(integrationId: number, externalSeriesId: string, force = true) {
  return apiRequest<ScanRun>("/api/v1/scans", {
    method: "POST",
    body: {
      scan_type: "series",
      integration_id: integrationId,
      external_series_id: externalSeriesId,
      force,
    },
  });
}

export function startFullScan(force = false) {
  return apiRequest<ScanRun>("/api/v1/scans", {
    method: "POST",
    body: { scan_type: "full", force },
  });
}

export function getScanHistory(signal?: AbortSignal) {
  return apiGet<ScanRun[]>("/api/v1/scans/history", signal);
}

export function cancelScan(scanRunId: number) {
  return apiRequest<ScanRun>(`/api/v1/scans/${scanRunId}/cancel`, { method: "POST" });
}
