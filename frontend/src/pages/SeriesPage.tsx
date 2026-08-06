import { Card } from "../components/ui/Card";
import { useI18n } from "../i18n/I18nProvider";

export function SeriesPage() {
  const { t } = useI18n();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">{t("series.title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t("series.subtitle")}</p>
      </div>
      <Card>
        <p className="text-sm text-muted-foreground">{t("common.empty")}</p>
      </Card>
    </div>
  );
}
