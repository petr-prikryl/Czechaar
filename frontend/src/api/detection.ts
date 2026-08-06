import { apiGet, apiRequest } from "./client";

export type CzechDetectionSettings = {
  language_codes: string[];
  title_indicators: string[];
};

export type CzechDetectionPreviewRequest = {
  language: string | null;
  title: string | null;
  settings: CzechDetectionSettings | null;
};

export type CzechDetectionPreviewResponse = {
  czech_match: boolean;
  match_reason: string;
  matched_value: string | null;
};

export function getDetectionSettings(signal?: AbortSignal) {
  return apiGet<CzechDetectionSettings>("/api/v1/czech-detection-settings", signal);
}

export function saveDetectionSettings(payload: CzechDetectionSettings) {
  return apiRequest<CzechDetectionSettings>("/api/v1/czech-detection-settings", {
    method: "PUT",
    body: payload,
  });
}

export function resetDetectionSettings() {
  return apiRequest<CzechDetectionSettings>("/api/v1/czech-detection-settings/reset", {
    method: "POST",
  });
}

export function previewDetection(payload: CzechDetectionPreviewRequest) {
  return apiRequest<CzechDetectionPreviewResponse>("/api/v1/czech-detection-settings/preview", {
    method: "POST",
    body: payload,
  });
}
