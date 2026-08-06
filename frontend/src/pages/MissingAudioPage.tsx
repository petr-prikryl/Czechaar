import { Card } from "../components/ui/Card";
import { useI18n } from "../i18n/I18nProvider";

export function MissingAudioPage() {
  const { t } = useI18n();

  return (
    <PageScaffold
      title={t("missing.title")}
      subtitle={t("missing.subtitle")}
      empty={t("common.empty")}
    />
  );
}

function PageScaffold({
  title,
  subtitle,
  empty,
}: {
  title: string;
  subtitle: string;
  empty: string;
}) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">{title}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
      </div>
      <Card>
        <p className="text-sm text-muted-foreground">{empty}</p>
      </Card>
    </div>
  );
}
