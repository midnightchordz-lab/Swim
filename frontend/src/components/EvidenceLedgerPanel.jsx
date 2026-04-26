import React from "react";
import { Database } from "lucide-react";

const EvidenceLedgerPanel = ({ ledger = [] }) => {
  if (!ledger.length) return null;

  return (
    <div data-testid="evidence-ledger-panel" className="bg-panel border border-sw rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Database className="w-4 h-4 text-sw-cyan" />
        <h3 className="text-sm font-bold text-sw">Evidence Ledger</h3>
      </div>
      <div className="space-y-2">
        {ledger.map((entry, index) => (
          <div key={`${entry.source}-${index}`} className="rounded-lg bg-sw3/40 border border-sw p-3">
            <div className="flex items-start justify-between gap-3 mb-1">
              <div>
                <p className="text-sm font-semibold text-sw">{entry.source}</p>
                <p className="text-[10px] uppercase tracking-wider text-sw3">{entry.type}</p>
              </div>
              <span className={`text-[10px] mono px-2 py-0.5 rounded ${
                String(entry.confidence_impact || "").startsWith("-")
                  ? "bg-red-500/15 text-red-400"
                  : "bg-emerald-500/15 text-sw-cyan"
              }`}>
                {entry.confidence_impact}
              </span>
            </div>
            <p className="text-xs text-sw2 leading-relaxed">{entry.notes}</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {(entry.used_for || []).map((item) => (
                <span key={item} className="text-[10px] px-1.5 py-0.5 rounded bg-sw-bg3 text-sw3">
                  {item}
                </span>
              ))}
            </div>
            {entry.freshness && (
              <p className="text-[10px] text-sw3 mt-2">
                Freshness: {new Date(entry.freshness).toLocaleString()}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default EvidenceLedgerPanel;
