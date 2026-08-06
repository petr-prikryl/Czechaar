import { apiRequest } from "./client";

export function ignoreMediaFile(mediaFileId: number) {
  return apiRequest("/api/v1/ignored", {
    method: "POST",
    body: { object_type: "media_file", object_id: mediaFileId },
  });
}
