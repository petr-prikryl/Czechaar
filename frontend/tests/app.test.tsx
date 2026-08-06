import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import { I18nProvider } from "../src/i18n/I18nProvider";
import { messages } from "../src/i18n/messages";

function renderApp() {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <I18nProvider>
        <MemoryRouter>
          <App />
        </MemoryRouter>
      </I18nProvider>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.spyOn(window, "fetch").mockResolvedValue(
    new Response(
      JSON.stringify({
        total_movies: 0,
        total_episodes: 0,
        total_media_files: 0,
        scanned_files: 0,
        files_with_czech_audio: 0,
        files_missing_czech_audio: 0,
        scan_errors: 0,
        files_without_mappings: 0,
        ignored_items: 0,
        stale_items: 0,
        last_synchronization_time: null,
        last_completed_scan_time: null,
        current_scan: null,
      }),
      { status: 200, headers: { "Content-Type": "application/json" } },
    ),
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("Czecharr shell", () => {
  it("renders Czech navigation by default", () => {
    window.localStorage.clear();
    renderApp();

    expect(screen.getAllByText("Přehled")[0]).toBeInTheDocument();
    expect(screen.getAllByText("Chybí české audio")[0]).toBeInTheDocument();
  });

  it("contains Czech and English translations for visible shell labels", () => {
    expect(messages.cs["settings.title"]).toBe("Nastavení");
    expect(messages.en["settings.title"]).toBe("Settings");
  });
});
