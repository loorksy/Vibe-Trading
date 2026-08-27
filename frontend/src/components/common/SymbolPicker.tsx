import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Search } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export interface OandaInstrument {
  canonical_id: string;
  display_symbol: string;
  asset_class: string;
  tradable: boolean;
}

interface SymbolPickerProps {
  value?: string;
  onChange: (canonicalId: string, displaySymbol: string) => void;
  className?: string;
}

export function SymbolPicker({ value, onChange, className }: SymbolPickerProps) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [instruments, setInstruments] = useState<OandaInstrument[]>([]);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.listOandaInstruments()
      .then(setInstruments)
      .catch(() => setInstruments([]));
  }, []);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return instruments;
    return instruments.filter(
      (i) =>
        i.display_symbol.toLowerCase().includes(q) ||
        i.canonical_id.toLowerCase().includes(q),
    );
  }, [instruments, query]);

  const selected = instruments.find((i) => i.canonical_id === value || i.display_symbol === value);

  return (
    <div ref={ref} className={cn("relative", className)}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm hover:bg-muted/50"
      >
        <Search className="h-4 w-4 text-muted-foreground" />
        <span className="font-mono">{selected?.display_symbol ?? t("symbolPicker.select")}</span>
      </button>
      {open && (
        <div className="absolute z-50 mt-1 w-72 rounded-lg border border-border bg-card shadow-lg">
          <div className="border-b border-border p-2">
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("symbolPicker.search")}
              className="w-full rounded-md bg-muted px-2 py-1.5 text-sm outline-none"
            />
          </div>
          <ul className="max-h-60 overflow-y-auto p-1">
            {filtered.map((inst) => (
              <li key={inst.canonical_id}>
                <button
                  type="button"
                  className="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-sm hover:bg-muted"
                  onClick={() => {
                    onChange(inst.canonical_id, inst.display_symbol);
                    setOpen(false);
                    setQuery("");
                  }}
                >
                  <span className="font-mono">{inst.display_symbol}</span>
                  <span className="text-xs text-muted-foreground">{inst.asset_class}</span>
                </button>
              </li>
            ))}
            {!filtered.length && (
              <li className="px-2 py-3 text-center text-xs text-muted-foreground">
                {t("symbolPicker.empty")}
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
