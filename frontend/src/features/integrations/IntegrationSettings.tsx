import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { PlugZap, Save, ShieldCheck, TestTube2 } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";

import {
  createIntegration,
  listIntegrations,
  type Integration,
  type IntegrationConnectionTestResponse,
  type IntegrationCreate,
  type IntegrationUpdate,
  type SourceType,
  testSavedIntegration,
  testUnsavedIntegration,
  updateIntegration,
} from "../../api/integrations";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { useI18n } from "../../i18n/I18nProvider";

const defaultForm: IntegrationCreate = {
  source_type: "radarr",
  name: "",
  base_url: "",
  web_url: "",
  api_key: "",
  api_key_env_var: "",
  enabled: true,
  timeout_seconds: 30,
  verify_tls: true,
};

function sourceLabel(sourceType: SourceType): string {
  return sourceType === "radarr" ? "Radarr" : "Sonarr";
}

export function IntegrationSettings() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [form, setForm] = useState<IntegrationCreate>(defaultForm);
  const [testResult, setTestResult] = useState<IntegrationConnectionTestResponse | null>(null);

  const integrationsQuery = useQuery({
    queryKey: ["integrations"],
    queryFn: ({ signal }) => listIntegrations(signal),
  });

  const createMutation = useMutation({
    mutationFn: createIntegration,
    onSuccess: () => {
      setForm(defaultForm);
      setTestResult(null);
      void queryClient.invalidateQueries({ queryKey: ["integrations"] });
    },
  });

  const unsavedTestMutation = useMutation({
    mutationFn: testUnsavedIntegration,
    onSuccess: setTestResult,
  });

  const savedTestMutation = useMutation({
    mutationFn: testSavedIntegration,
    onSuccess: setTestResult,
  });
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: IntegrationUpdate }) =>
      updateIntegration(id, payload),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["integrations"] }),
  });

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    createMutation.mutate({
      ...form,
      name: form.name.trim(),
      base_url: form.base_url.trim(),
      web_url: form.web_url?.trim() || null,
      api_key: form.api_key?.trim() || null,
      api_key_env_var: form.api_key_env_var?.trim() || null,
    });
  };

  const testCurrent = () => {
    unsavedTestMutation.mutate({
      ...form,
      web_url: form.web_url?.trim() || null,
      api_key: form.api_key?.trim() || null,
      api_key_env_var: form.api_key_env_var?.trim() || null,
    });
  };

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_420px]">
      <Card className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold">{t("settings.integrations")}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{t("settings.integrationsHelp")}</p>
          </div>
          <PlugZap aria-hidden="true" className="text-muted-foreground" size={20} />
        </div>

        {integrationsQuery.isLoading ? (
          <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
        ) : null}
        {integrationsQuery.isError ? (
          <p className="text-sm text-rose-600">{t("settings.integrationsLoadError")}</p>
        ) : null}
        {integrationsQuery.data?.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("settings.noIntegrations")}</p>
        ) : null}

        <div className="space-y-3">
          {integrationsQuery.data?.map((integration) => (
            <IntegrationRow
              key={integration.id}
              integration={integration}
              testing={savedTestMutation.isPending}
              onTest={() => savedTestMutation.mutate(integration.id)}
              saving={updateMutation.isPending}
              onSaveWebUrl={(webUrl) =>
                updateMutation.mutate({
                  id: integration.id,
                  payload: { web_url: webUrl.trim() || null },
                })
              }
            />
          ))}
        </div>
      </Card>

      <Card>
        <form className="space-y-4" onSubmit={submit}>
          <div>
            <h2 className="text-base font-semibold">{t("settings.addIntegration")}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{t("settings.apiKeySafe")}</p>
          </div>

          <label className="block space-y-1 text-sm">
            <span className="font-medium">{t("settings.sourceType")}</span>
            <select
              className="h-10 w-full rounded-md border border-border bg-background px-3"
              value={form.source_type}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  source_type: event.target.value as SourceType,
                }))
              }
            >
              <option value="radarr">Radarr</option>
              <option value="sonarr">Sonarr</option>
            </select>
          </label>

          <label className="block space-y-1 text-sm">
            <span className="font-medium">{t("settings.displayName")}</span>
            <input
              className="h-10 w-full rounded-md border border-border bg-background px-3"
              value={form.name}
              onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              required
            />
          </label>

          <label className="block space-y-1 text-sm">
            <span className="font-medium">{t("settings.baseUrl")}</span>
            <input
              className="h-10 w-full rounded-md border border-border bg-background px-3"
              value={form.base_url}
              onChange={(event) =>
                setForm((current) => ({ ...current, base_url: event.target.value }))
              }
              placeholder="https://radarr.example.test"
              required
            />
          </label>

          <label className="block space-y-1 text-sm">
            <span className="font-medium">{t("settings.webUrl")}</span>
            <input
              className="h-10 w-full rounded-md border border-border bg-background px-3"
              value={form.web_url ?? ""}
              onChange={(event) =>
                setForm((current) => ({ ...current, web_url: event.target.value }))
              }
              placeholder="https://radarr.prikryl.cc"
            />
            <span className="text-xs text-muted-foreground">{t("settings.webUrlHelp")}</span>
          </label>

          <label className="block space-y-1 text-sm">
            <span className="font-medium">{t("settings.apiKey")}</span>
            <input
              className="h-10 w-full rounded-md border border-border bg-background px-3"
              type="password"
              value={form.api_key ?? ""}
              onChange={(event) =>
                setForm((current) => ({ ...current, api_key: event.target.value }))
              }
              autoComplete="off"
            />
          </label>

          <label className="block space-y-1 text-sm">
            <span className="font-medium">{t("settings.apiKeyEnvVar")}</span>
            <input
              className="h-10 w-full rounded-md border border-border bg-background px-3"
              value={form.api_key_env_var ?? ""}
              onChange={(event) =>
                setForm((current) => ({ ...current, api_key_env_var: event.target.value }))
              }
              placeholder="RADARR_API_KEY"
            />
          </label>

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block space-y-1 text-sm">
              <span className="font-medium">{t("settings.timeout")}</span>
              <input
                className="h-10 w-full rounded-md border border-border bg-background px-3"
                type="number"
                min={1}
                max={300}
                value={form.timeout_seconds}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    timeout_seconds: Number(event.target.value),
                  }))
                }
              />
            </label>
            <div className="space-y-2 pt-6">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.enabled}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, enabled: event.target.checked }))
                  }
                />
                {t("settings.enabled")}
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.verify_tls}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, verify_tls: event.target.checked }))
                  }
                />
                {t("settings.verifyTls")}
              </label>
            </div>
          </div>

          {testResult ? <ConnectionResult result={testResult} /> : null}
          {createMutation.isError || unsavedTestMutation.isError || savedTestMutation.isError ? (
            <p className="text-sm text-rose-600">{t("settings.requestFailed")}</p>
          ) : null}

          <div className="flex flex-wrap gap-2">
            <Button type="submit" disabled={createMutation.isPending}>
              <Save aria-hidden="true" size={16} />
              {t("settings.saveIntegration")}
            </Button>
            <Button
              variant="secondary"
              onClick={testCurrent}
              disabled={unsavedTestMutation.isPending}
            >
              <TestTube2 aria-hidden="true" size={16} />
              {t("settings.testConnection")}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

function IntegrationRow({
  integration,
  testing,
  onTest,
  saving,
  onSaveWebUrl,
}: {
  integration: Integration;
  testing: boolean;
  onTest: () => void;
  saving: boolean;
  onSaveWebUrl: (webUrl: string) => void;
}) {
  const { t } = useI18n();
  const [webUrl, setWebUrl] = useState(integration.web_url ?? "");

  useEffect(() => {
    setWebUrl(integration.web_url ?? "");
  }, [integration.web_url]);

  return (
    <div className="flex flex-col gap-3 rounded-md border border-border p-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-medium">{integration.name}</p>
          <Badge>{sourceLabel(integration.source_type)}</Badge>
          <Badge tone={integration.api_key_configured ? "success" : "warning"}>
            <ShieldCheck aria-hidden="true" className="mr-1" size={13} />
            {integration.api_key_configured
              ? t("settings.apiKeyConfigured")
              : t("settings.apiKeyMissing")}
          </Badge>
        </div>
        <p className="mt-1 truncate text-sm text-muted-foreground">{integration.base_url}</p>
        <div className="mt-2 flex max-w-2xl flex-col gap-2 sm:flex-row">
          <label className="sr-only" htmlFor={`web-url-${integration.id}`}>
            {t("settings.webUrl")}
          </label>
          <input
            id={`web-url-${integration.id}`}
            className="h-9 min-w-0 flex-1 rounded-md border border-border bg-background px-3 text-sm"
            value={webUrl}
            onChange={(event) => setWebUrl(event.target.value)}
            placeholder={t("settings.webUrlPlaceholder")}
          />
          <Button
            variant="secondary"
            onClick={() => onSaveWebUrl(webUrl)}
            disabled={saving || webUrl.trim() === (integration.web_url ?? "")}
          >
            <Save aria-hidden="true" size={14} />
            {t("settings.saveWebUrl")}
          </Button>
        </div>
      </div>
      <Button variant="secondary" onClick={onTest} disabled={testing}>
        <TestTube2 aria-hidden="true" size={16} />
        {t("settings.testConnection")}
      </Button>
    </div>
  );
}

function ConnectionResult({ result }: { result: IntegrationConnectionTestResponse }) {
  return (
    <div className="rounded-md border border-border bg-muted p-3 text-sm">
      <Badge tone={result.ok ? "success" : "danger"}>{result.ok ? "OK" : result.error_code}</Badge>
      <p className="mt-2 text-muted-foreground">{result.message}</p>
      {result.version ? (
        <p className="mt-1 text-muted-foreground">
          {result.application} {result.version}
        </p>
      ) : null}
    </div>
  );
}
