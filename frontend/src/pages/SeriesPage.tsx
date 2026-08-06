import { useQuery } from "@tanstack/react-query";
import { ChevronDown } from "lucide-react";
import { useState } from "react";

import { getEpisodes, getSeries } from "../api/media";
import { StatusBadge } from "../components/StatusBadge";
import { useI18n } from "../i18n/I18nProvider";
import { formatEpisodeCode } from "../utils/format";

export function SeriesPage() {
  const { t } = useI18n();
  const [expanded, setExpanded] = useState<string | null>(null);
  const seriesQuery = useQuery({
    queryKey: ["series"],
    queryFn: ({ signal }) => getSeries(signal),
  });
  const episodesQuery = useQuery({
    queryKey: ["episodes", expanded],
    queryFn: ({ signal }) => getEpisodes(expanded, signal),
    enabled: expanded !== null,
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
        {seriesQuery.data?.map((series) => (
          <section
            key={series.external_series_id}
            className="rounded-lg border border-border bg-background"
          >
            <button
              className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
              onClick={() =>
                setExpanded((current) =>
                  current === series.external_series_id ? null : series.external_series_id,
                )
              }
            >
              <span className="font-medium">{series.title}</span>
              <span className="flex items-center gap-3 text-sm text-muted-foreground">
                {series.episode_count} {t("series.episodes")}
                <StatusBadge status={series.errors > 0 ? "error" : "completed"} />
                <ChevronDown aria-hidden="true" size={16} />
              </span>
            </button>
            {expanded === series.external_series_id ? (
              <div className="border-t border-border">
                {episodesQuery.data?.items.map((episode) => (
                  <div
                    key={episode.id}
                    className="grid gap-2 px-4 py-2 text-sm md:grid-cols-[90px_1fr_160px]"
                  >
                    <span>{formatEpisodeCode(episode.season_number, episode.episode_number)}</span>
                    <span>{episode.title}</span>
                    <StatusBadge status={episode.media_file?.scan_state} />
                  </div>
                ))}
              </div>
            ) : null}
          </section>
        ))}
        {seriesQuery.data?.length === 0 ? (
          <p className="rounded-lg border border-border bg-background p-4 text-sm text-muted-foreground">
            {t("common.empty")}
          </p>
        ) : null}
      </div>
    </div>
  );
}
