import { apiGet, apiRequest } from "./client";

export type LibrarySyncRun = {
  id: number;
  source_type: string | null;
  integration_id: number | null;
  status: string;
  started_at: string;
  finished_at: string | null;
  items_total: number;
  files_total: number;
  stale_count: number;
  error_message: string | null;
};

export function syncLibrary() {
  return apiRequest<LibrarySyncRun>("/api/v1/sync/library", {
    method: "POST",
    body: {},
  });
}

export function getSyncHistory(signal?: AbortSignal) {
  return apiGet<LibrarySyncRun[]>("/api/v1/sync/history", signal);
}
