import { Check } from "lucide-react";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { IntegrationSettings } from "../features/integrations/IntegrationSettings";
import { useI18n } from "../i18n/I18nProvider";

export function SettingsPage() {
  const { locale, setLocale, t } = useI18n();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">{t("settings.title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t("settings.subtitle")}</p>
      </div>
      <IntegrationSettings />

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
