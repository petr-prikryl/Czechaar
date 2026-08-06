import { apiGet, apiRequest } from "./client";

export type SourceType = "radarr" | "sonarr";

export type Integration = {
  id: number;
  source_type: SourceType;
  name: string;
  base_url: string;
  web_url: string | null;
  enabled: boolean;
  timeout_seconds: number;
  verify_tls: boolean;
  api_key_env_var: string | null;
  api_key_configured: boolean;
  last_test_at: string | null;
  created_at: string;
  updated_at: string;
};

export type IntegrationCreate = {
  source_type: SourceType;
  name: string;
  base_url: string;
  web_url?: string | null;
  api_key?: string | null;
  api_key_env_var?: string | null;
  enabled: boolean;
  timeout_seconds: number;
  verify_tls: boolean;
};

export type IntegrationUpdate = Partial<
  Pick<
    IntegrationCreate,
    | "name"
    | "base_url"
    | "web_url"
    | "api_key"
    | "api_key_env_var"
    | "enabled"
    | "timeout_seconds"
    | "verify_tls"
  >
>;

export type IntegrationConnectionTestResponse = {
  ok: boolean;
  status_code: number | null;
  error_code: string | null;
  message: string;
  application: string | null;
  version: string | null;
};

export function listIntegrations(signal?: AbortSignal) {
  return apiGet<Integration[]>("/api/v1/integrations", signal);
}

export function createIntegration(payload: IntegrationCreate) {
  return apiRequest<Integration>("/api/v1/integrations", {
    method: "POST",
    body: payload,
  });
}

export function updateIntegration(integrationId: number, payload: IntegrationUpdate) {
  return apiRequest<Integration>(`/api/v1/integrations/${integrationId}`, {
    method: "PATCH",
    body: payload,
  });
}

export function testUnsavedIntegration(payload: IntegrationCreate) {
  return apiRequest<IntegrationConnectionTestResponse>("/api/v1/integrations/test", {
    method: "POST",
    body: payload,
  });
}

export function testSavedIntegration(integrationId: number) {
  return apiRequest<IntegrationConnectionTestResponse>(
    `/api/v1/integrations/${integrationId}/test`,
    {
      method: "POST",
    },
  );
}
