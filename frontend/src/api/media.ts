import { apiGet } from "./client";

export type MediaFileSummary = {
  id: number;
  external_file_id: string;
  original_source_path: string;
  mapped_local_path: string | null;
  relative_path: string | null;
  size: number | null;
  quality: string | null;
  quality_profile: string | null;
  scan_state: string;
  czech_audio_result: boolean | null;
  last_successful_scan: string | null;
  last_scan_attempt: string | null;
  error_code: string | null;
  sanitized_error_message: string | null;
  stale: boolean;
};

export type MediaItem = {
  id: number;
  integration_id: number;
  source_type: "radarr" | "sonarr";
  external_item_id: string;
  external_series_id: string | null;
  media_type: "movie" | "episode";
  title: string;
  original_title: string | null;
  series_title: string | null;
  year: number | null;
  season_number: number | null;
  episode_number: number | null;
  absolute_episode_number: number | null;
  monitored: boolean;
  file_presence: boolean;
  upstream_status: string | null;
  poster_url: string | null;
  stale: boolean;
  media_file: MediaFileSummary | null;
};

export type MediaItemPage = {
  items: MediaItem[];
  page: number;
  page_size: number;
  total: number;
};

export type SeriesSummary = {
  external_series_id: string;
  title: string;
  integration_id: number;
  monitored: boolean;
  episode_count: number;
  files_scanned: number;
  episodes_missing_czech_audio: number;
  errors: number;
  poster_url: string | null;
  stale: boolean;
};

export function getMissingAudio(params: URLSearchParams, signal?: AbortSignal) {
  return apiGet<MediaItemPage>(`/api/v1/missing?${params.toString()}`, signal);
}

export function getMovies(signal?: AbortSignal) {
  return apiGet<MediaItemPage>("/api/v1/movies?page_size=100&sort=title", signal);
}

export function getEpisodes(seriesId: string | null, signal?: AbortSignal) {
  const params = new URLSearchParams({ page_size: "100", sort: "season_number" });
  if (seriesId) {
    params.set("series", seriesId);
  }
  return apiGet<MediaItemPage>(`/api/v1/episodes?${params.toString()}`, signal);
}

export function getSeries(signal?: AbortSignal) {
  return apiGet<SeriesSummary[]>("/api/v1/series", signal);
}
