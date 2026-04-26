import React from "react";
import { BarChart3, Shield } from "lucide-react";

const label = {
  support: "Support",
  opposition: "Opposition",
  undecided: "Undecided",
  insufficient_data: "Insufficient data",
};

const EnsembleForecastPanel = ({ ensemble }) => {
  if (!ensemble || !ensemble.runs) return null;

  const consensus = ensemble.consensus || {};
  const variance = ensemble.variance || {};
  const rows = ["support", "opposition", "undecided"];

  return (
    <div data-testid="ensemble-forecast-panel" className="bg-panel border border-sw rounded-xl p-4">
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <BarChart3 className="w-4 h-4 text-sw-cyan" />
        <h3 className="text-sm font-bold text-sw">Ensemble Forecast</h3>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-sw-cyan/15 text-sw-cyan border border-sw-cyan/30">
          {ensemble.runs} BOOTSTRAP RUNS
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-3">
        <div className="rounded-lg bg-sw3/40 border border-sw p-2">
          <p className="text-[10px] text-sw3 uppercase tracking-wider">Dominant</p>
          <p className="text-sm text-sw font-semibold">{label[ensemble.dominant_outcome] || ensemble.dominant_outcome}</p>
        </div>
        <div className="rounded-lg bg-sw3/40 border border-sw p-2">
          <p className="text-[10px] text-sw3 uppercase tracking-wider">Stability</p>
          <p className="text-sm mono text-sw-cyan">{ensemble.stability_score}%</p>
        </div>
        <div className="rounded-lg bg-sw3/40 border border-sw p-2">
          <p className="text-[10px] text-sw3 uppercase tracking-wider">Sample Size</p>
          <p className="text-sm mono text-sw">{ensemble.sample_size}</p>
        </div>
      </div>

      <div className="space-y-2">
        {rows.map((key) => (
          <div key={key}>
            <div className="flex justify-between text-[10px] mb-1">
              <span className="text-sw2">{label[key]}</span>
              <span className="mono text-sw">{consensus[key] || 0}% · var {variance[key] || 0}</span>
            </div>
            <div className="h-2 bg-sw-bg3 rounded-full overflow-hidden">
              <div
                className={`h-full ${key === "support" ? "bg-emerald-500" : key === "opposition" ? "bg-red-500" : "bg-sw3"}`}
                style={{ width: `${consensus[key] || 0}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 flex items-start gap-2 text-xs text-sw2">
        <Shield className="w-3.5 h-3.5 mt-0.5 text-amber-400 flex-shrink-0" />
        <span>{ensemble.interpretation}</span>
      </div>
    </div>
  );
};

export default EnsembleForecastPanel;
