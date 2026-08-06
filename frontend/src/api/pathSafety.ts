import { apiGet, apiRequest } from "./client";
import type { SourceType } from "./integrations";

export type PathMapping = {
  id: number;
  integration_id: number | null;
  source_type: SourceType | null;
  remote_path_prefix: string;
  local_path_prefix: string;
  enabled: boolean;
  priority: number;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type PathMappingCreate = {
  integration_id: number | null;
  source_type: SourceType | null;
  remote_path_prefix: string;
  local_path_prefix: string;
  enabled: boolean;
  priority: number;
  description: string | null;
};

export type PathMappingTestRequest = {
  remote_path: string;
  source_type: SourceType;
  integration_id: number;
};

export type PathMappingTestResponse = {
  original_path: string;
  mapped_path: string | null;
  mapping_id: number | null;
  status: string;
  inside_allowed_root: boolean | null;
};

export type MediaRoot = {
  id: number;
  path: string;
  enabled: boolean;
  description: string | null;
  exists: boolean;
  readable: boolean;
  created_at: string;
  updated_at: string;
};

export type MediaRootCreate = {
  path: string;
  enabled: boolean;
  description: string | null;
};

export function listPathMappings(signal?: AbortSignal) {
  return apiGet<PathMapping[]>("/api/v1/path-mappings", signal);
}

export function createPathMapping(payload: PathMappingCreate) {
  return apiRequest<PathMapping>("/api/v1/path-mappings", { method: "POST", body: payload });
}

export function deletePathMapping(mappingId: number) {
  return apiRequest<void>(`/api/v1/path-mappings/${mappingId}`, { method: "DELETE" });
}

export function testPathMapping(payload: PathMappingTestRequest) {
  return apiRequest<PathMappingTestResponse>("/api/v1/path-mappings/test", {
    method: "POST",
    body: payload,
  });
}

export function listMediaRoots(signal?: AbortSignal) {
  return apiGet<MediaRoot[]>("/api/v1/media-roots", signal);
}

export function createMediaRoot(payload: MediaRootCreate) {
  return apiRequest<MediaRoot>("/api/v1/media-roots", { method: "POST", body: payload });
}

export function deleteMediaRoot(rootId: number) {
  return apiRequest<void>(`/api/v1/media-roots/${rootId}`, { method: "DELETE" });
}
