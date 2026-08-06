import { useQuery } from "@tanstack/react-query";
import { Activity, AlertTriangle, CheckCircle2, Database, Film, Tv, VolumeX } from "lucide-react";

import { getDashboardStats } from "../api/dashboard";
import { Card } from "../components/ui/Card";
import { useI18n } from "../i18n/I18nProvider";

export function DashboardPage() {
  const { t } = useI18n();
  const statsQuery = useQuery({
    queryKey: ["dashboard"],
    queryFn: ({ signal }) => getDashboardStats(signal),
  });
  const stats = statsQuery.data;
  const cards = [
    { label: "dashboard.totalMovies", value: stats?.total_movies ?? 0, icon: Film },
    { label: "dashboard.totalEpisodes", value: stats?.total_episodes ?? 0, icon: Tv },
    { label: "dashboard.scannedFiles", value: stats?.scanned_files ?? 0, icon: Database },
    { label: "dashboard.withCzech", value: stats?.files_with_czech_audio ?? 0, icon: CheckCircle2 },
    {
      label: "dashboard.missingAudio",
      value: stats?.files_missing_czech_audio ?? 0,
      icon: VolumeX,
    },
    { label: "dashboard.scanErrors", value: stats?.scan_errors ?? 0, icon: AlertTriangle },
  ] as const;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">{t("dashboard.title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t("dashboard.subtitle")}</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {cards.map((card) => (
          <Card key={card.label}>
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-muted-foreground">{t(card.label)}</p>
              <card.icon aria-hidden="true" className="text-muted-foreground" size={18} />
            </div>
            <p className="mt-2 text-3xl font-semibold">{card.value.toLocaleString()}</p>
          </Card>
        ))}
      </div>
      <Card>
        {statsQuery.isLoading ? (
          <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
        ) : null}
        {stats?.current_scan ? (
          <div className="flex items-center gap-3 text-sm">
            <Activity aria-hidden="true" size={18} />
            <span>
              {stats.current_scan.completed_item_count}/{stats.current_scan.requested_item_count}{" "}
              {stats.current_scan.current_status}
            </span>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">{t("dashboard.noActiveScan")}</p>
        )}
      </Card>
    </div>
  );
}
