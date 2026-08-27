import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { CalendarClock, Loader2, Newspaper } from "lucide-react";
import { SymbolPicker } from "@/components/common/SymbolPicker";
import { safeGet, safeSet } from "@/lib/storage";
import { cn } from "@/lib/utils";

const SYMBOL_KEY = "vibe-selected-symbol";

export function Today() {
  const { t } = useTranslation();
  const [symbol, setSymbol] = useState(() => safeGet(SYMBOL_KEY) || "");
  const [displaySymbol, setDisplaySymbol] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = window.setTimeout(() => setLoading(false), 400);
    return () => window.clearTimeout(timer);
  }, [symbol]);

  const handleSymbol = (canonicalId: string, label: string) => {
    setSymbol(canonicalId);
    setDisplaySymbol(label);
    safeSet(SYMBOL_KEY, canonicalId);
  };

  return (
    <div className="mx-auto max-w-5xl p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {t("layout.daily")}
          </p>
          <h1 className="text-2xl font-semibold tracking-tight">{t("today.title")}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{t("today.subtitle")}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">{t("today.benchmark")}</span>
          <SymbolPicker value={symbol} onChange={handleSymbol} />
        </div>
      </div>

      {displaySymbol && (
        <p className="text-sm text-muted-foreground">
          {t("today.scanning", { symbol: displaySymbol })}
        </p>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-lg border border-border/60 bg-card p-4">
          <div className="mb-3 flex items-center gap-2">
            <Newspaper className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold">{t("today.news")}</h2>
          </div>
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              {t("today.loading")}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">{t("today.newsEmpty")}</p>
          )}
        </section>

        <section className="rounded-lg border border-border/60 bg-card p-4">
          <div className="mb-3 flex items-center gap-2">
            <CalendarClock className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold">{t("today.calendar")}</h2>
          </div>
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              {t("today.loading")}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">{t("today.calendarEmpty")}</p>
          )}
        </section>
      </div>

      <p className={cn("text-xs text-muted-foreground")}>{t("today.hint")}</p>
    </div>
  );
}
