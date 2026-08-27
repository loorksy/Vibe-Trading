import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { safeGet } from "@/lib/storage";

const SYMBOL_KEY = "vibe-selected-symbol";

export function FeedHealthBanner() {
  const { t } = useTranslation();
  const [unreliable, setUnreliable] = useState(false);

  useEffect(() => {
    const symbol = safeGet(SYMBOL_KEY) || "EUR_USD";
    api.getFeedHealth(symbol)
      .then((health) => setUnreliable(!health.reliable))
      .catch(() => setUnreliable(true));
  }, []);

  if (!unreliable) return null;
  return (
    <div className="flex items-center gap-2 border-b border-amber-500/30 bg-amber-500/10 px-4 py-2 text-xs text-amber-700 dark:text-amber-300">
      <AlertTriangle className="h-4 w-4 shrink-0" />
      <span>{t("desk.feedUnreliable")}</span>
    </div>
  );
}
