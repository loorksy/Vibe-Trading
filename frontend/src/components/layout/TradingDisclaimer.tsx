import { useTranslation } from "react-i18next";

export function TradingDisclaimer() {
  const { t } = useTranslation();
  return (
    <p className="text-center text-[11px] text-muted-foreground px-4 py-2">
      {t("desk.disclaimer")}
    </p>
  );
}
