import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RotateCcw, Save, TestTube2 } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";

import {
  getDetectionSettings,
  previewDetection,
  resetDetectionSettings,
  saveDetectionSettings,
  type CzechDetectionPreviewResponse,
  type CzechDetectionSettings,
} from "../../api/detection";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { useI18n } from "../../i18n/I18nProvider";

function splitValues(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function joinValues(values: string[]): string {
  return values.join(", ");
}

export function DetectionSettings() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [languageCodes, setLanguageCodes] = useState("");
  const [titleIndicators, setTitleIndicators] = useState("");
  const [previewLanguage, setPreviewLanguage] = useState("");
  const [previewTitle, setPreviewTitle] = useState("");
  const [previewResult, setPreviewResult] = useState<CzechDetectionPreviewResponse | null>(null);

  const settingsQuery = useQuery({
    queryKey: ["czech-detection-settings"],
    queryFn: ({ signal }) => getDetectionSettings(signal),
  });

  useEffect(() => {
    if (settingsQuery.data) {
      setLanguageCodes(joinValues(settingsQuery.data.language_codes));
      setTitleIndicators(joinValues(settingsQuery.data.title_indicators));
    }
  }, [settingsQuery.data]);

  const currentSettings = (): CzechDetectionSettings => ({
    language_codes: splitValues(languageCodes),
    title_indicators: splitValues(titleIndicators),
  });

  const saveMutation = useMutation({
    mutationFn: saveDetectionSettings,
    onSuccess: (settings) => {
      queryClient.setQueryData(["czech-detection-settings"], settings);
    },
  });
  const resetMutation = useMutation({
    mutationFn: resetDetectionSettings,
    onSuccess: (settings) => {
      queryClient.setQueryData(["czech-detection-settings"], settings);
      setLanguageCodes(joinValues(settings.language_codes));
      setTitleIndicators(joinValues(settings.title_indicators));
    },
  });
  const previewMutation = useMutation({
    mutationFn: previewDetection,
    onSuccess: setPreviewResult,
  });

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    saveMutation.mutate(currentSettings());
  };

  return (
    <Card className="space-y-4">
      <div>
        <h2 className="text-base font-semibold">{t("settings.czechDetection")}</h2>
      </div>

      {settingsQuery.isLoading ? (
        <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
      ) : null}

      <form className="space-y-3" onSubmit={submit}>
        <label className="block space-y-1 text-sm">
          <span className="font-medium">{t("settings.languageCodes")}</span>
          <input
            className="h-10 w-full rounded-md border border-border bg-background px-3"
            value={languageCodes}
            onChange={(event) => setLanguageCodes(event.target.value)}
            required
          />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="font-medium">{t("settings.titleIndicators")}</span>
          <textarea
            className="min-h-24 w-full rounded-md border border-border bg-background px-3 py-2"
            value={titleIndicators}
            onChange={(event) => setTitleIndicators(event.target.value)}
            required
          />
        </label>
        <div className="flex flex-wrap gap-2">
          <Button type="submit" disabled={saveMutation.isPending}>
            <Save aria-hidden="true" size={16} />
            {t("settings.saveDetection")}
          </Button>
          <Button
            variant="secondary"
            onClick={() => resetMutation.mutate()}
            disabled={resetMutation.isPending}
          >
            <RotateCcw aria-hidden="true" size={16} />
            {t("settings.resetDefaults")}
          </Button>
        </div>
      </form>

      <div className="space-y-3 border-t border-border pt-4">
        <h3 className="text-sm font-semibold">{t("settings.previewDetection")}</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <input
            className="h-10 rounded-md border border-border bg-background px-3 text-sm"
            value={previewLanguage}
            onChange={(event) => setPreviewLanguage(event.target.value)}
            placeholder="ces"
            aria-label={t("settings.previewLanguage")}
          />
          <input
            className="h-10 rounded-md border border-border bg-background px-3 text-sm"
            value={previewTitle}
            onChange={(event) => setPreviewTitle(event.target.value)}
            placeholder="Cesky dabing"
            aria-label={t("settings.previewTitle")}
          />
        </div>
        <Button
          variant="secondary"
          onClick={() =>
            previewMutation.mutate({
              language: previewLanguage.trim() || null,
              title: previewTitle.trim() || null,
              settings: currentSettings(),
            })
          }
          disabled={previewMutation.isPending}
        >
          <TestTube2 aria-hidden="true" size={16} />
          {t("settings.previewDetection")}
        </Button>
        {previewResult ? (
          <div className="rounded-md border border-border bg-muted p-3 text-sm">
            <Badge tone={previewResult.czech_match ? "success" : "warning"}>
              {previewResult.czech_match ? t("dashboard.withCzech") : t("dashboard.missingAudio")}
            </Badge>
            <p className="mt-2 text-muted-foreground">
              {previewResult.match_reason}
              {previewResult.matched_value ? `: ${previewResult.matched_value}` : ""}
            </p>
          </div>
        ) : null}
      </div>
    </Card>
  );
}
