import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronRight, ExternalLink, RotateCw } from "lucide-react";
import { useState } from "react";

import { getEpisodes, getSeries, getSeriesSeasons } from "../api/media";
import { startMediaFileScan, startSeriesScan } from "../api/scans";
import { StatusBadge } from "../components/StatusBadge";
import { Button } from "../components/ui/Button";
import { useI18n } from "../i18n/I18nProvider";
import { formatEpisodeCode } from "../utils/format";

export function SeriesPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [expandedSeries, setExpandedSeries] = useState<{
    key: string;
    integrationId: number;
    externalSeriesId: string;
  } | null>(null);
  const [expandedSeason, setExpandedSeason] = useState<string | null>(null);
  const seriesQuery = useQuery({
    queryKey: ["series"],
    queryFn: ({ signal }) => getSeries(signal),
  });
  const seasonsQuery = useQuery({
    queryKey: ["series-seasons", expandedSeries?.integrationId, expandedSeries?.externalSeriesId],
    queryFn: ({ signal }) =>
      getSeriesSeasons(expandedSeries!.integrationId, expandedSeries!.externalSeriesId, signal),
    enabled: expandedSeries !== null,
  });
  const episodesQuery = useQuery({
    queryKey: [
      "episodes",
      expandedSeries?.integrationId,
      expandedSeries?.externalSeriesId,
      expandedSeason,
    ],
    queryFn: ({ signal }) =>
      getEpisodes(
        {
          integrationId: expandedSeries!.integrationId,
          seriesId: expandedSeries!.externalSeriesId,
          season: expandedSeason === "unknown" ? null : Number(expandedSeason),
          pageSize: 100,
        },
        signal,
      ),
    enabled: expandedSeries !== null && expandedSeason !== null,
  });
  const invalidateSeriesViews = () => {
    void queryClient.invalidateQueries({ queryKey: ["series"] });
    void queryClient.invalidateQueries({ queryKey: ["series-seasons"] });
    void queryClient.invalidateQueries({ queryKey: ["episodes"] });
    void queryClient.invalidateQueries({ queryKey: ["missing"] });
  };
  const rescanSeriesMutation = useMutation({
    mutationFn: (series: { integrationId: number; externalSeriesId: string }) =>
      startSeriesScan(series.integrationId, series.externalSeriesId, true),
    onSuccess: invalidateSeriesViews,
  });
  const rescanEpisodeMutation = useMutation({
    mutationFn: (mediaFileId: number) => startMediaFileScan(mediaFileId, true),
    onSuccess: invalidateSeriesViews,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">{t("series.title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t("series.subtitle")}</p>
      </div>
      <div className="space-y-3">
        {seriesQuery.isLoading ? (
          <p className="rounded-lg border border-border bg-background p-4 text-sm text-muted-foreground">
            {t("common.loading")}
          </p>
        ) : null}
        {seriesQuery.data?.map((series) => {
          const seriesKey = `${series.integration_id}:${series.external_series_id}`;
          const isSeriesExpanded = expandedSeries?.key === seriesKey;
          return (
            <section key={seriesKey} className="rounded-lg border border-border bg-background">
              <div className="flex w-full flex-wrap items-center justify-between gap-3 px-4 py-3">
                <button
                  className="flex min-w-0 flex-1 items-center gap-2 text-left"
                  onClick={() => {
                    setExpandedSeason(null);
                    setExpandedSeries((current) =>
                      current?.key === seriesKey
                        ? null
                        : {
                            key: seriesKey,
                            integrationId: series.integration_id,
                            externalSeriesId: series.external_series_id,
                          },
                    );
                  }}
                >
                  <span className="shrink-0">
                    {isSeriesExpanded ? (
                      <ChevronDown aria-hidden="true" size={16} />
                    ) : (
                      <ChevronRight aria-hidden="true" size={16} />
                    )}
                  </span>
                  <span className="min-w-0 truncate font-medium">{series.title}</span>
                </button>
                <span className="flex items-center gap-3 text-sm text-muted-foreground">
                  {series.episode_count} {t("series.episodes")}
                  <StatusBadge status={series.errors > 0 ? "error" : "completed"} />
                </span>
                <Button
                  className="h-8 px-2"
                  disabled={rescanSeriesMutation.isPending}
                  variant="secondary"
                  onClick={() =>
                    rescanSeriesMutation.mutate({
                      integrationId: series.integration_id,
                      externalSeriesId: series.external_series_id,
                    })
                  }
                >
                  <RotateCw aria-hidden="true" size={14} />
                  {t("actions.rescan")}
                </Button>
              </div>
              {isSeriesExpanded ? (
                <div className="space-y-2 border-t border-border p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2 px-1">
                    <p className="text-sm text-muted-foreground">
                      {series.files_scanned} {t("series.filesScanned")} ·{" "}
                      {series.episodes_missing_czech_audio} {t("series.missingEpisodes")} ·{" "}
                      {series.errors} {t("series.errors")}
                    </p>
                    {series.source_web_url ? (
                      <a
                        className="inline-flex h-8 items-center gap-2 rounded-md border border-border px-2 text-xs font-medium hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                        href={series.source_web_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <ExternalLink aria-hidden="true" size={13} />
                        {t("actions.openSonarr")}
                      </a>
                    ) : null}
                  </div>
                  {seasonsQuery.isLoading ? (
                    <p className="px-1 py-2 text-sm text-muted-foreground">{t("common.loading")}</p>
                  ) : null}
                  {seasonsQuery.data?.map((season) => {
                    const seasonKey =
                      season.season_number === null ? "unknown" : String(season.season_number);
                    const isSeasonExpanded = expandedSeason === seasonKey;
                    return (
                      <div key={seasonKey} className="rounded-md border border-border">
                        <button
                          className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left"
                          onClick={() =>
                            setExpandedSeason((current) =>
                              current === seasonKey ? null : seasonKey,
                            )
                          }
                        >
                          <span className="flex items-center gap-2 text-sm font-medium">
                            {isSeasonExpanded ? (
                              <ChevronDown aria-hidden="true" size={15} />
                            ) : (
                              <ChevronRight aria-hidden="true" size={15} />
                            )}
                            {season.season_number === null
                              ? t("series.unknownSeason")
                              : `${t("series.season")} ${season.season_number}`}
                          </span>
                          <span className="flex items-center gap-3 text-xs text-muted-foreground">
                            {season.episode_count} {t("series.episodes")}
                            {season.episodes_missing_czech_audio} {t("series.missingEpisodes")}
                          </span>
                        </button>
                        {isSeasonExpanded ? (
                          <div className="border-t border-border">
                            {episodesQuery.isLoading ? (
                              <p className="px-4 py-3 text-sm text-muted-foreground">
                                {t("common.loading")}
                              </p>
                            ) : null}
                            {episodesQuery.data?.items.map((episode) => (
                              <div
                                key={episode.id}
                                className="grid gap-2 px-4 py-2 text-sm md:grid-cols-[90px_1fr_160px_140px]"
                              >
                                <span>
                                  {formatEpisodeCode(episode.season_number, episode.episode_number)}
                                </span>
                                <span>{episode.title}</span>
                                <StatusBadge status={episode.media_file?.scan_state} />
                                {episode.media_file ? (
                                  <Button
                                    className="h-8 justify-self-start px-2"
                                    disabled={rescanEpisodeMutation.isPending}
                                    variant="secondary"
                                    onClick={() =>
                                      rescanEpisodeMutation.mutate(episode.media_file!.id)
                                    }
                                  >
                                    <RotateCw aria-hidden="true" size={14} />
                                    {t("actions.rescan")}
                                  </Button>
                                ) : (
                                  <span />
                                )}
                              </div>
                            ))}
                            {episodesQuery.data?.items.length === 0 ? (
                              <p className="px-4 py-3 text-sm text-muted-foreground">
                                {t("common.empty")}
                              </p>
                            ) : null}
                          </div>
                        ) : null}
                      </div>
                    );
                  })}
                  {seasonsQuery.data?.length === 0 ? (
                    <p className="px-1 py-2 text-sm text-muted-foreground">{t("common.empty")}</p>
                  ) : null}
                </div>
              ) : null}
            </section>
          );
        })}
        {seriesQuery.data?.length === 0 ? (
          <p className="rounded-lg border border-border bg-background p-4 text-sm text-muted-foreground">
            {t("common.empty")}
          </p>
        ) : null}
      </div>
    </div>
  );
}
