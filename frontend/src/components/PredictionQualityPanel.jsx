import React from "react";
import { Shield, Clock, Database, AlertTriangle } from "lucide-react";

const pct = (value) => `${Math.round((value || 0) * 100)}%`;
const signedPct = (value) => `${value >= 0 ? "+" : ""}${Math.round((value || 0) * 100)}%`;

const strengthStyles = {
  strong: "bg-emerald-500/15 border-emerald-500/40 text-sw-cyan",
  moderate: "bg-amber-500/15 border-amber-500/40 text-amber-400",
  limited: "bg-red-500/15 border-red-500/40 text-red-400",
};

const PredictionQualityPanel = ({ quality }) => {
  if (!quality) return null;

  const reliability = quality.simulation_reliability || {};
  const freshness = quality.data_freshness || {};
  const interval = quality.confidence_interval || {};
  const strength = quality.evidence_strength || "limited";
  const calibration = quality.calibration || {};

  return (
    <div data-testid="prediction-quality-panel" className="bg-panel border border-sw rounded-xl p-4">
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <Shield className="w-4 h-4 text-sw-cyan" />
        <h3 className="text-sm font-bold text-sw">Prediction Quality</h3>
        <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${strengthStyles[strength] || strengthStyles.limited}`}>
          {strength.toUpperCase()} EVIDENCE
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
        <div className="rounded-lg bg-sw3/40 border border-sw p-2">
          <p className="text-[10px] text-sw3 uppercase tracking-wider">Evidence</p>
          <p className="text-sm mono text-sw">{pct(quality.evidence_score)}</p>
        </div>
        <div className="rounded-lg bg-sw3/40 border border-sw p-2">
          <p className="text-[10px] text-sw3 uppercase tracking-wider">Uncertainty</p>
          <p className="text-sm mono text-sw">{pct(quality.uncertainty)}</p>
        </div>
        <div className="rounded-lg bg-sw3/40 border border-sw p-2">
          <p className="text-[10px] text-sw3 uppercase tracking-wider">Confidence Band</p>
          <p className="text-sm mono text-sw">{pct(interval.low)}-{pct(interval.high)}</p>
        </div>
        <div className="rounded-lg bg-sw3/40 border border-sw p-2">
          <p className="text-[10px] text-sw3 uppercase tracking-wider">Fallbacks</p>
          <p className="text-sm mono text-sw">{reliability.fallback_posts || 0}</p>
        </div>
      </div>

      {calibration.calibrated_confidence_score != null && (
        <div className="mb-3 rounded-lg bg-sw3/30 border border-sw p-3">
          <p className="text-[10px] text-sw3 uppercase tracking-wider mb-1">Confidence Calibration</p>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="mono text-sw2">Raw {pct(calibration.raw_confidence_score)}</span>
            <span className="text-sw3">-></span>
            <span className="mono text-sw">Calibrated {pct(calibration.calibrated_confidence_score)}</span>
            <span className={`px-1.5 py-0.5 rounded ${
              calibration.adjustment >= 0 ? "bg-emerald-500/15 text-sw-cyan" : "bg-amber-500/15 text-amber-400"
            }`}>
              {signedPct(calibration.adjustment)} adjustment
            </span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
        <div className="flex items-start gap-2 text-sw2">
          <Database className="w-3.5 h-3.5 mt-0.5 text-sw-cyan" />
          <span>
            {reliability.total_posts || 0} posts analyzed
            {freshness.market_data_points ? `, ${freshness.market_data_points} market data point(s)` : ""}
            {freshness.real_social_sources?.length ? `, real sources: ${freshness.real_social_sources.join(", ")}` : ""}
          </span>
        </div>
        <div className="flex items-start gap-2 text-sw2">
          <Clock className="w-3.5 h-3.5 mt-0.5 text-amber-400" />
          <span>{freshness.latest_input_at ? `Latest input: ${new Date(freshness.latest_input_at).toLocaleString()}` : "No timestamped live inputs available"}</span>
        </div>
      </div>

      {quality.evidence_drivers?.length > 0 && (
        <div className="mt-3">
          <p className="text-[10px] text-sw3 uppercase tracking-wider mb-2">Evidence Drivers</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {quality.evidence_drivers.map((driver, idx) => (
              <div key={idx} className="rounded-lg bg-sw3/30 border border-sw p-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs text-sw">{driver.name}</span>
                  <span className={`text-[10px] mono ${String(driver.impact || "").startsWith("-") ? "text-red-400" : "text-sw-cyan"}`}>
                    {driver.impact}
                  </span>
                </div>
                <p className="text-[10px] text-sw3 mt-0.5">{driver.status}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {quality.caveats?.length > 0 && (
        <div className="mt-3 space-y-1">
          {quality.caveats.slice(0, 3).map((item, idx) => (
            <div key={idx} className="flex items-start gap-2 text-[11px] text-sw3">
              <AlertTriangle className="w-3 h-3 mt-0.5 text-amber-400 flex-shrink-0" />
              <span>{item}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PredictionQualityPanel;
