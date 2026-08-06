import { Card } from "../components/ui/Card";
import { useI18n } from "../i18n/I18nProvider";

const dashboardCards = [
  { label: "dashboard.totalMovies", value: "0" },
  { label: "dashboard.totalEpisodes", value: "0" },
  { label: "dashboard.scannedFiles", value: "0" },
  { label: "dashboard.missingAudio", value: "0" },
] as const;

export function DashboardPage() {
  const { t } = useI18n();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">{t("dashboard.title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t("dashboard.subtitle")}</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {dashboardCards.map((card) => (
          <Card key={card.label}>
            <p className="text-sm text-muted-foreground">{t(card.label)}</p>
            <p className="mt-2 text-3xl font-semibold">{card.value}</p>
          </Card>
        ))}
      </div>
      <Card>
        <p className="text-sm text-muted-foreground">{t("status.foundation")}</p>
      </Card>
    </div>
  );
}
