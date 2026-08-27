import { Link } from "react-router";
import { useTranslation } from "react-i18next";
import { FlaskConical, Layers, LineChart, Settings2 } from "lucide-react";

const cards = [
  { to: "/alpha-zoo", icon: Layers, titleKey: "build.alphaZoo", bodyKey: "build.alphaZooBody" },
  { to: "/scheduled", icon: FlaskConical, titleKey: "build.scheduled", bodyKey: "build.scheduledBody" },
  { to: "/reports", icon: LineChart, titleKey: "build.reports", bodyKey: "build.reportsBody" },
  { to: "/settings", icon: Settings2, titleKey: "build.settings", bodyKey: "build.settingsBody" },
] as const;

export function Build() {
  const { t } = useTranslation();

  return (
    <div className="mx-auto max-w-5xl p-6 space-y-6">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {t("layout.daily")}
        </p>
        <h1 className="text-2xl font-semibold tracking-tight">{t("build.title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t("build.subtitle")}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {cards.map(({ to, icon: Icon, titleKey, bodyKey }) => (
          <Link
            key={to}
            to={to}
            className="group rounded-lg border border-border/60 bg-card p-4 transition hover:border-primary/40 hover:bg-muted/30"
          >
            <div className="mb-2 flex items-center gap-2">
              <Icon className="h-4 w-4 text-primary" />
              <h2 className="text-sm font-semibold group-hover:text-primary">{t(titleKey)}</h2>
            </div>
            <p className="text-sm text-muted-foreground">{t(bodyKey)}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
