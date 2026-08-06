import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { IntegrationSettings } from "../src/features/integrations/IntegrationSettings";
import { I18nProvider } from "../src/i18n/I18nProvider";

function renderIntegrations() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <I18nProvider>
        <IntegrationSettings />
      </I18nProvider>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("IntegrationSettings", () => {
  it("shows API-key configured state without exposing the key", async () => {
    vi.spyOn(window, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            id: 1,
            source_type: "radarr",
            name: "Main Radarr",
            base_url: "https://radarr.example.test",
            enabled: true,
            timeout_seconds: 30,
            verify_tls: true,
            api_key_env_var: null,
            api_key_configured: true,
            last_test_at: null,
            created_at: "2026-08-06T10:00:00Z",
            updated_at: "2026-08-06T10:00:00Z",
          },
        ]),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    renderIntegrations();

    expect(await screen.findByText("Main Radarr")).toBeInTheDocument();
    expect(screen.getByText("API klíč nastaven")).toBeInTheDocument();
    expect(screen.queryByText("secret-key")).not.toBeInTheDocument();
  });

  it("submits a new integration from the form", async () => {
    const fetchMock = vi.spyOn(window, "fetch");
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            id: 2,
            source_type: "sonarr",
            name: "Main Sonarr",
            base_url: "https://sonarr.example.test",
            enabled: true,
            timeout_seconds: 30,
            verify_tls: true,
            api_key_env_var: null,
            api_key_configured: true,
            last_test_at: null,
            created_at: "2026-08-06T10:00:00Z",
            updated_at: "2026-08-06T10:00:00Z",
          }),
          { status: 201, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));

    renderIntegrations();
    await screen.findByText("Zatím není nastavená žádná integrace.");

    await userEvent.selectOptions(screen.getByLabelText("Typ zdroje"), "sonarr");
    await userEvent.type(screen.getByLabelText("Zobrazovaný název"), "Main Sonarr");
    await userEvent.type(screen.getByLabelText("Základní URL"), "https://sonarr.example.test");
    await userEvent.type(screen.getByLabelText("API klíč"), "secret-key");
    await userEvent.click(screen.getByRole("button", { name: /Uložit integraci/ }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    const [, createCall] = fetchMock.mock.calls;
    expect(createCall[0]).toBe("/api/v1/integrations");
    expect(createCall[1]?.method).toBe("POST");
    expect(createCall[1]?.body).toContain('"api_key":"secret-key"');
  });
});
