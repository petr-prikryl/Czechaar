import { apiGet, apiRequest } from "./client";

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
  source_web_url: string | null;
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
  source_web_url: string | null;
};

export type SeasonSummary = {
  integration_id: number;
  external_series_id: string;
  season_number: number | null;
  episode_count: number;
  files_scanned: number;
  episodes_missing_czech_audio: number;
  errors: number;
  stale: boolean;
};

export type AudioStream = {
  id: number;
  media_file_id: number;
  stream_index: number;
  codec_name: string | null;
  codec_long_name: string | null;
  channels: number | null;
  channel_layout: string | null;
  sample_rate: number | null;
  bit_rate: number | null;
  original_language: string | null;
  normalized_language: string | null;
  original_title: string | null;
  normalized_title: string | null;
  czech_match: boolean;
  match_reason: string;
  matched_value: string | null;
};

export type FfmpegRepairPlan = {
  media_file_id: number;
  audio_stream_id: number;
  audio_stream_index: number;
  audio_stream_ordinal: number;
  input_path: string;
  output_path: string;
  command: string[];
  display_command: string;
  warning: string;
};

export function getMissingAudio(params: URLSearchParams, signal?: AbortSignal) {
  return apiGet<MediaItemPage>(`/api/v1/missing?${params.toString()}`, signal);
}

export function getMovies(page = 1, pageSize = 50, signal?: AbortSignal) {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
    sort: "title",
  });
  return apiGet<MediaItemPage>(`/api/v1/movies?${params.toString()}`, signal);
}

export function getEpisodes(
  options: {
    seriesId?: string | null;
    integrationId?: number;
    season?: number | null;
    page?: number;
    pageSize?: number;
  } = {},
  signal?: AbortSignal,
) {
  const params = new URLSearchParams({
    page: String(options.page ?? 1),
    page_size: String(options.pageSize ?? 100),
    sort: options.season === undefined ? "season_number" : "episode_number",
  });
  if (options.seriesId) {
    params.set("series", options.seriesId);
  }
  if (options.integrationId !== undefined) {
    params.set("integration_id", String(options.integrationId));
  }
  if (options.season !== undefined && options.season !== null) {
    params.set("season", String(options.season));
  }
  return apiGet<MediaItemPage>(`/api/v1/episodes?${params.toString()}`, signal);
}

export function getSeries(signal?: AbortSignal) {
  return apiGet<SeriesSummary[]>("/api/v1/series", signal);
}

export function getSeriesSeasons(
  integrationId: number,
  externalSeriesId: string,
  signal?: AbortSignal,
) {
  return apiGet<SeasonSummary[]>(
    `/api/v1/series/${integrationId}/${encodeURIComponent(externalSeriesId)}/seasons`,
    signal,
  );
}

export function getAudioStreams(mediaFileId: number, signal?: AbortSignal) {
  return apiGet<AudioStream[]>(`/api/v1/media-files/${mediaFileId}/audio-streams`, signal);
}

export function createFfmpegRepairPlan(mediaFileId: number, audioStreamId: number) {
  return apiRequest<FfmpegRepairPlan>(`/api/v1/media-files/${mediaFileId}/ffmpeg-repair-plan`, {
    method: "POST",
    body: {
      audio_stream_id: audioStreamId,
      language_code: "cze",
      title: "Čeština",
    },
  });
}
