import { useTranslation } from "react-i18next";
import { AlertTriangle } from "lucide-react";

export function FeedHealthBanner() {
  const { t } = useTranslation();
  // Shown when operator has not confirmed OANDA credentials in Settings.
  const show = false;
  if (!show) return null;
  return (
    <div className="flex items-center gap-2 border-b border-amber-500/30 bg-amber-500/10 px-4 py-2 text-xs text-amber-700 dark:text-amber-300">
      <AlertTriangle className="h-4 w-4 shrink-0" />
      <span>{t("desk.feedUnreliable")}</span>
    </div>
  );
}
