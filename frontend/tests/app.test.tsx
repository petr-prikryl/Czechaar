import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

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
