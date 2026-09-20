import React from "react";
import { Escalation } from "@/types";

interface EscalationBannerProps {
  escalations: Escalation[];
}

export const EscalationBanner: React.FC<EscalationBannerProps> = ({ escalations }) => {
  if (!escalations || escalations.length === 0) return null;

  return (
    <div className="bg-red-50 border-2 border-red-300 text-red-900 rounded-card p-5 shadow-sm space-y-3">
      <div className="flex items-center gap-2 border-b border-red-200 pb-2">
        <svg
          className="w-5 h-5 text-red-700 flex-shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <h2 className="text-sm font-bold tracking-wider uppercase text-red-950">
          Support Escalation Alert ({escalations.length})
        </h2>
      </div>

      <div className="space-y-2.5">
        {escalations.map((esc) => (
          <div
            key={esc.id}
            className="bg-red-100/70 border border-red-300 rounded-xl p-3.5 text-xs text-red-950 flex flex-col gap-1.5"
          >
            <div className="flex justify-between items-center">
              <span className="font-extrabold text-xs uppercase bg-red-800 text-white px-2.5 py-0.5 rounded-full tracking-wide">
                Reason Code: {esc.reason_code}
              </span>
              <span className="text-[10px] uppercase font-bold text-red-800">
                Status: {esc.status}
              </span>
            </div>
            <p className="font-medium text-red-900 leading-relaxed mt-1">
              {esc.summary}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
