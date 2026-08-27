import { memo, useState } from "react";
import { Check, ShieldAlert, TrendingDown, TrendingUp } from "lucide-react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { api, type TradeRecommendation } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Props {
  recommendation: TradeRecommendation;
}

export const TradeRecommendationCard = memo(function TradeRecommendationCard({
  recommendation,
}: Props) {
  const { t } = useTranslation();
  const [volume, setVolume] = useState("0.01");
  const [status, setStatus] = useState(recommendation.status);
  const [busy, setBusy] = useState(false);

  const isBuy = recommendation.direction === "BUY";
  const executable =
    status === "pending" &&
    recommendation.publishable &&
    recommendation.execution_status === "ready";

  async function execute() {
    const lots = Number(volume);
    if (!Number.isFinite(lots) || lots <= 0) {
      toast.error(t("trade.invalidVolume"));
      return;
    }
    setBusy(true);
    try {
      const result = await api.executeTrade({
        recommendation_id: recommendation.recommendation_id,
        volume: lots,
        session_id: recommendation.session_id,
        consent_ack: true,
      });
      setStatus(result.recommendation.status);
      toast.success(t("trade.executed"));
    } catch (err) {
      toast.error(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  if (status === "executed") {
    return (
      <div className="mx-auto flex max-w-2xl items-center gap-2 rounded-xl border border-border/60 bg-muted/35 px-4 py-3 text-sm">
        <Check className="h-4 w-4 text-success" />
        <span className="font-medium">{recommendation.display_symbol}</span>
        <span className="text-muted-foreground">{t("trade.executedBadge")}</span>
      </div>
    );
  }

  return (
    <section className="mx-auto max-w-2xl rounded-2xl border border-primary/25 bg-card p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-primary">
            {t("trade.recommendationTitle")}
          </p>
          <h3 className="mt-1 flex items-center gap-2 font-semibold">
            {isBuy ? (
              <TrendingUp className="h-4 w-4 text-success" />
            ) : (
              <TrendingDown className="h-4 w-4 text-danger" />
            )}
            <span className="font-mono">{recommendation.display_symbol}</span>
            <span className={cn("text-sm", isBuy ? "text-success" : "text-danger")}>
              {recommendation.direction}
            </span>
          </h3>
        </div>
        <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] uppercase text-muted-foreground">
          {recommendation.execution_status}
        </span>
      </div>

      <dl className="mt-4 grid gap-2 rounded-xl bg-muted/40 p-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-muted-foreground">{t("trade.entryZone")}</dt>
          <dd className="font-mono">
            {recommendation.entry_zone?.[0]} – {recommendation.entry_zone?.[1]}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">{t("trade.stopLoss")}</dt>
          <dd className="font-mono">{recommendation.stop_loss}</dd>
        </div>
      </dl>

      {recommendation.gate_results?.length > 0 && (
        <ul className="mt-3 space-y-1">
          {recommendation.gate_results.map((gate) => (
            <li
              key={gate.gate}
              className={cn(
                "flex items-center gap-2 text-xs",
                gate.passed ? "text-muted-foreground" : "text-amber-600 dark:text-amber-300",
              )}
            >
              <ShieldAlert className="h-3 w-3 shrink-0" />
              <span className="font-medium">{gate.gate}</span>
              <span>— {gate.reason}</span>
            </li>
          ))}
        </ul>
      )}

      {executable ? (
        <div className="mt-4 flex flex-wrap items-end gap-2">
          <label className="text-xs text-muted-foreground">
            {t("trade.volumeLots")}
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={volume}
              onChange={(e) => setVolume(e.target.value)}
              className="mt-1 block w-28 rounded-md border bg-background px-2 py-1.5 text-sm"
            />
          </label>
          <button
            type="button"
            disabled={busy}
            onClick={execute}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {busy ? t("trade.executing") : t("trade.execute")}
          </button>
        </div>
      ) : (
        <p className="mt-4 text-xs text-muted-foreground">{t("trade.notExecutable")}</p>
      )}
    </section>
  );
});
