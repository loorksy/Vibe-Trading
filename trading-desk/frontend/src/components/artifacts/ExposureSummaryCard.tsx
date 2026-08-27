interface ExposureSummaryProps {
  data: {
    total_risk_r?: number;
    positions?: number;
    by_symbol?: Record<string, number>;
    warnings?: string[];
  };
}

export function ExposureSummaryCard({ data }: ExposureSummaryProps) {
  return (
    <div className="mt-3 rounded-xl border border-amber-500/30 bg-amber-500/5 p-4">
      <h4 className="text-sm font-semibold text-amber-300">Portfolio Exposure</h4>
      <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
        <div>
          <span className="text-gray-500">Total risk</span>
          <p className="font-mono text-lg">{data.total_risk_r ?? 0}R</p>
        </div>
        <div>
          <span className="text-gray-500">Open positions</span>
          <p className="font-mono text-lg">{data.positions ?? 0}</p>
        </div>
      </div>
      {data.warnings?.map((w, i) => (
        <p key={i} className="mt-2 text-xs text-amber-400">⚠ {w}</p>
      ))}
    </div>
  );
}
