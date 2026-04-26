import React from "react";
import { CheckCircle, Loader2, AlertCircle } from "lucide-react";

const clampPercent = (value) => Math.max(0, Math.min(100, Math.round(value || 0)));

const ProgressStatusCard = ({
  title,
  subtitle,
  detail,
  current = 0,
  total = 100,
  percent,
  countLabel,
  status = "running",
}) => {
  const computedPercent = percent != null
    ? clampPercent(percent)
    : clampPercent(total > 0 ? (current / total) * 100 : 0);
  const isDone = status === "done";
  const isError = status === "error";

  const Icon = isDone ? CheckCircle : isError ? AlertCircle : Loader2;
  const iconClass = isDone ? "text-sw-cyan" : isError ? "text-red-400" : "text-amber-400 animate-spin";
  const barClass = isError ? "bg-red-500" : isDone ? "bg-sw-cyan" : "bg-amber-400";

  return (
    <div data-testid="progress-status-card" className="bg-panel border border-sw rounded-lg p-3">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-start gap-2 min-w-0">
          <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${iconClass}`} />
          <div className="min-w-0">
            <p className="text-sm text-sw font-semibold">{title}</p>
            {subtitle && <p className="text-xs text-sw2 mt-0.5">{subtitle}</p>}
            {detail && <p className="text-[11px] text-sw3 mt-1">{detail}</p>}
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <p className="text-sm text-sw-cyan mono font-bold">{computedPercent}%</p>
          {countLabel && <p className="text-[10px] text-sw3">{countLabel}</p>}
        </div>
      </div>
      <div className="h-2 bg-sw-bg3 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ${barClass}`}
          style={{ width: `${computedPercent}%` }}
        />
      </div>
    </div>
  );
};

export default ProgressStatusCard;
