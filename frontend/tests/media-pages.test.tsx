import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DashboardPage } from "../src/pages/DashboardPage";
import { MissingAudioPage } from "../src/pages/MissingAudioPage";
import { MoviesPage } from "../src/pages/MoviesPage";
import { ScanHistoryPage } from "../src/pages/ScanHistoryPage";
import { SeriesPage } from "../src/pages/SeriesPage";
import type { ScanRun } from "../src/api/scans";
import { I18nProvider } from "../src/i18n/I18nProvider";

const mediaPage = {
  page: 1,
  page_size: 100,
  total: 1,
  items: [
    {
      id: 1,
      integration_id: 1,
      source_type: "radarr",
      external_item_id: "10",
      external_series_id: null,
      media_type: "movie",
      title: "Avatar",
      original_title: "Avatar",
      series_title: null,
      year: 2009,
      season_number: null,
      episode_number: null,
      absolute_episode_number: null,
      monitored: true,
      file_presence: true,
      upstream_status: "released",
      poster_url: null,
      stale: false,
      source_web_url: "https://radarr.example.test/movie/avatar-2009",
      media_file: {
        id: 2,
        external_file_id: "20",
        original_source_path: "/data/movies/Avatar.mkv",
        mapped_local_path: "/movies/Avatar.mkv",
        relative_path: "Avatar.mkv",
        size: 1234,
        quality: "Bluray-1080p",
        quality_profile: "HD",
        scan_state: "czech_audio_missing",
        czech_audio_result: false,
        last_successful_scan: null,
        last_scan_attempt: "2026-08-06T10:00:00Z",
        error_code: null,
        sanitized_error_message: null,
        stale: false,
      },
    },
  ],
};

const episodePage = {
  ...mediaPage,
  items: [
    {
      ...mediaPage.items[0],
      id: 11,
      source_type: "sonarr",
      external_item_id: "101",
      external_series_id: "7",
      media_type: "episode",
      title: "Part One",
      series_title: "Demo Show",
      season_number: 1,
      episode_number: 2,
      source_web_url: "https://sonarr.example.test/series/demo-show",
    },
  ],
};

function renderPage(page: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <I18nProvider>{page}</I18nProvider>
    </QueryClientProvider>,
  );
}

const defaultScanHistory: ScanRun[] = [
  {
    id: 3,
    scan_type: "full",
    source_type: null,
    integration_id: null,
    status: "running",
    requested_item_count: 10,
    completed_item_count: 4,
    success_count: 2,
    missing_czech_count: 1,
    cache_hit_count: 1,
    error_count: 0,
    cancellation_requested: false,
    current_status: "scanned 4/10",
    error_summary: null,
    started_at: "2026-08-06T10:00:00Z",
    finished_at: null,
    created_at: "2026-08-06T10:00:00Z",
  },
];

function mockApi(scanHistory = defaultScanHistory) {
  return vi.spyOn(window, "fetch").mockImplementation((input) => {
    const url =
      typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
    if (url.startsWith("/api/v1/dashboard")) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            total_movies: 4,
            total_episodes: 9,
            total_media_files: 13,
            scanned_files: 10,
            files_with_czech_audio: 6,
            files_missing_czech_audio: 4,
            scan_errors: 1,
            files_without_mappings: 1,
            ignored_items: 2,
            stale_items: 0,
            last_synchronization_time: null,
            last_completed_scan_time: null,
            current_scan: null,
          }),
          { status: 200 },
        ),
      );
    }
    if (url.startsWith("/api/v1/missing")) {
      return Promise.resolve(new Response(JSON.stringify(mediaPage), { status: 200 }));
    }
    if (url.startsWith("/api/v1/media-files/2/audio-streams")) {
      return Promise.resolve(
        new Response(
          JSON.stringify([
            {
              id: 1,
              media_file_id: 2,
              stream_index: 0,
              codec_name: "aac",
              channels: 2,
              original_language: "eng",
              normalized_language: "eng",
              original_title: "English 2.0",
              normalized_title: "english 2.0",
              czech_match: false,
              match_reason: "no_match",
              matched_value: null,
            },
          ]),
          { status: 200 },
        ),
      );
    }
    if (url.startsWith("/api/v1/movies")) {
      return Promise.resolve(new Response(JSON.stringify(mediaPage), { status: 200 }));
    }
    if (url.startsWith("/api/v1/series/1/7/seasons")) {
      return Promise.resolve(
        new Response(
          JSON.stringify([
            {
              integration_id: 1,
              external_series_id: "7",
              season_number: 1,
              episode_count: 2,
              files_scanned: 1,
              episodes_missing_czech_audio: 1,
              errors: 0,
              stale: false,
            },
          ]),
          { status: 200 },
        ),
      );
    }
    if (url.startsWith("/api/v1/series")) {
      return Promise.resolve(
        new Response(
          JSON.stringify([
            {
              external_series_id: "7",
              title: "Demo Show",
              integration_id: 1,
              monitored: true,
              episode_count: 2,
              files_scanned: 1,
              episodes_missing_czech_audio: 1,
              errors: 0,
              poster_url: null,
              stale: false,
              source_web_url: "https://sonarr.example.test/series/demo-show",
            },
          ]),
          { status: 200 },
        ),
      );
    }
    if (url.startsWith("/api/v1/episodes")) {
      return Promise.resolve(new Response(JSON.stringify(episodePage), { status: 200 }));
    }
    if (url.startsWith("/api/v1/scans/history")) {
      return Promise.resolve(new Response(JSON.stringify(scanHistory), { status: 200 }));
    }
    if (url.startsWith("/api/v1/sync/library")) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            id: 4,
            source_type: null,
            integration_id: null,
            status: "completed",
            started_at: "2026-08-06T10:01:00Z",
            finished_at: "2026-08-06T10:01:05Z",
            items_total: 3,
            files_total: 2,
            stale_count: 0,
            error_message: null,
          }),
          { status: 200 },
        ),
      );
    }
    if (url.startsWith("/api/v1/ignored") || url.startsWith("/api/v1/scans")) {
      return Promise.resolve(new Response(JSON.stringify({ ok: true }), { status: 201 }));
    }
    return Promise.resolve(new Response("{}", { status: 200 }));
  });
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("media pages", () => {
  it("renders dashboard statistics", async () => {
    mockApi();
    renderPage(<DashboardPage />);

    const moviesCard = (await screen.findByText("Filmy")).closest("section");

    expect(moviesCard).not.toBeNull();
    await waitFor(() =>
      expect(within(moviesCard as HTMLElement).getByText("4")).toBeInTheDocument(),
    );
    expect(screen.getByText("České audio nalezeno")).toBeInTheDocument();
  });

  it("renders missing audio and supports ignore action", async () => {
    const fetchMock = mockApi();
    renderPage(<MissingAudioPage />);

    expect(await screen.findByText("Avatar")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Ignorovat/ }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith("/api/v1/ignored", expect.anything()),
    );
  });

  it("expands missing audio diagnostics lazily", async () => {
    mockApi();
    renderPage(<MissingAudioPage />);

    await userEvent.click(await screen.findByRole("button", { name: /diagnostiku/ }));

    expect(await screen.findByText(/nevyhovuje/)).toBeInTheDocument();
    expect(screen.getByText("English 2.0")).toBeInTheDocument();
    expect(screen.getByText("no_match")).toBeInTheDocument();
  });

  it("renders the movie table", async () => {
    mockApi();
    renderPage(<MoviesPage />);

    expect(await screen.findByText("Avatar")).toBeInTheDocument();
    expect(screen.getByText("Bluray-1080p")).toBeInTheDocument();
  });

  it("expands series seasons and episodes", async () => {
    mockApi();
    renderPage(<SeriesPage />);

    await userEvent.click(await screen.findByText("Demo Show"));
    await userEvent.click(await screen.findByText(/Sez/));

    expect(await screen.findByText("S01E02")).toBeInTheDocument();
    expect(screen.getByText("Part One")).toBeInTheDocument();
  });

  it("renders active scan progress", async () => {
    mockApi();
    renderPage(<ScanHistoryPage />);

    expect(await screen.findByText("4/10")).toBeInTheDocument();
    expect(screen.getByText("running")).toBeInTheDocument();
  });

  it("starts library synchronization from scan history", async () => {
    const fetchMock = mockApi();
    renderPage(<ScanHistoryPage />);

    await userEvent.click(await screen.findByRole("button", { name: /Synchronizovat knihovnu/ }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/sync/library",
        expect.objectContaining({ method: "POST" }),
      ),
    );
    expect(await screen.findByText(/Synchronizace dokončena:/)).toBeInTheDocument();
  });

  it("explains empty scan runs", async () => {
    mockApi([
      {
        ...defaultScanHistory[0],
        id: 4,
        status: "completed",
        requested_item_count: 0,
        completed_item_count: 0,
        current_status: "no_media_files",
        finished_at: "2026-08-06T10:01:00Z",
      },
    ]);
    renderPage(<ScanHistoryPage />);

    expect(await screen.findByText("Žádné soubory ke skenování")).toBeInTheDocument();
    expect(screen.getByText(/Poslední sken nenašel žádné soubory/)).toBeInTheDocument();
  });
});
