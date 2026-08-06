import { useQuery } from "@tanstack/react-query";
import { Check } from "lucide-react";

import { getRuntimeSettings, getVersion } from "../api/system";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { IntegrationSettings } from "../features/integrations/IntegrationSettings";
import { DetectionSettings } from "../features/settings/DetectionSettings";
import { PathSafetySettings } from "../features/settings/PathSafetySettings";
import { useI18n } from "../i18n/I18nProvider";

export function SettingsPage() {
  const { locale, setLocale, t } = useI18n();
  const versionQuery = useQuery({
    queryKey: ["version"],
    queryFn: ({ signal }) => getVersion(signal),
  });
  const runtimeSettingsQuery = useQuery({
    queryKey: ["runtime-settings"],
    queryFn: ({ signal }) => getRuntimeSettings(signal),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">{t("settings.title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t("settings.subtitle")}</p>
      </div>
      <IntegrationSettings />
      <PathSafetySettings />
      <DetectionSettings />

      <Card className="space-y-3">
        <h2 className="text-base font-semibold">{t("settings.scanning")}</h2>
        {runtimeSettingsQuery.isLoading ? (
          <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
        ) : runtimeSettingsQuery.isError || !runtimeSettingsQuery.data ? (
          <p className="text-sm text-red-600">{t("common.error")}</p>
        ) : (
          <dl className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <dt className="text-muted-foreground">{t("settings.ffprobePath")}</dt>
              <dd className="font-medium">{runtimeSettingsQuery.data.ffprobe_path}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">{t("settings.ffprobeTimeout")}</dt>
              <dd className="font-medium">{runtimeSettingsQuery.data.ffprobe_timeout}s</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">{t("settings.scanConcurrency")}</dt>
              <dd className="font-medium">{runtimeSettingsQuery.data.scan_concurrency}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">{t("settings.scheduledScans")}</dt>
              <dd className="font-medium">
                {runtimeSettingsQuery.data.scheduled_scan_enabled
                  ? t("common.enabled")
                  : t("common.disabled")}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">{t("settings.scheduleInterval")}</dt>
              <dd className="font-medium">
                {runtimeSettingsQuery.data.scheduled_scan_interval_minutes} min
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">{t("settings.staleRetention")}</dt>
              <dd className="font-medium">
                {runtimeSettingsQuery.data.stale_retention_days} {t("settings.days")}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">{t("settings.timezone")}</dt>
              <dd className="font-medium">{runtimeSettingsQuery.data.timezone}</dd>
            </div>
          </dl>
        )}
      </Card>

      <Card className="space-y-3">
        <h2 className="text-base font-semibold">{t("settings.about")}</h2>
        {versionQuery.isLoading ? (
          <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
        ) : versionQuery.isError || !versionQuery.data ? (
          <p className="text-sm text-red-600">{t("common.error")}</p>
        ) : (
          <dl className="grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-muted-foreground">{t("settings.applicationVersion")}</dt>
              <dd className="font-medium">{versionQuery.data.version}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">{t("settings.apiVersion")}</dt>
              <dd className="font-medium">{versionQuery.data.api_version}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">{t("settings.gitCommit")}</dt>
              <dd className="font-medium">{versionQuery.data.git_commit ?? "unknown"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">{t("settings.buildDate")}</dt>
              <dd className="font-medium">{versionQuery.data.build_date ?? "unknown"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">{t("settings.demoMode")}</dt>
              <dd className="font-medium">
                {versionQuery.data.demo_mode ? t("common.enabled") : t("common.disabled")}
              </dd>
            </div>
          </dl>
        )}
      </Card>

      <Card className="space-y-3">
        <h2 className="text-base font-semibold">{t("common.language")}</h2>
        <div className="flex flex-wrap gap-2">
          <Button
            variant={locale === "cs" ? "primary" : "secondary"}
            onClick={() => setLocale("cs")}
          >
            {locale === "cs" ? <Check aria-hidden="true" size={16} /> : null}
            {t("common.czech")}
          </Button>
          <Button
            variant={locale === "en" ? "primary" : "secondary"}
            onClick={() => setLocale("en")}
          >
            {locale === "en" ? <Check aria-hidden="true" size={16} /> : null}
            {t("common.english")}
          </Button>
        </div>
      </Card>
    </div>
  );
}
