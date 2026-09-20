import React from "react";
import { DecisionTraceItem } from "@/types";

interface DecisionTracePanelProps {
  decisionTrace: DecisionTraceItem[];
}

export const DecisionTracePanel: React.FC<DecisionTracePanelProps> = ({
  decisionTrace,
}) => {
  return (
    <div className="bg-amber-50 border-2 border-amber-300 text-amber-950 rounded-card p-5 shadow-sm space-y-3">
      <div className="flex justify-between items-center border-b border-amber-200 pb-2">
        <h2 className="text-sm font-bold tracking-wider uppercase text-amber-950">
          Policy decision (from rules engine)
        </h2>
        <span className="text-[10px] uppercase font-bold bg-amber-200 text-amber-900 px-2 py-0.5 rounded-full">
          Deterministic Rules Engine
        </span>
      </div>

      {!decisionTrace || decisionTrace.length === 0 ? (
        <p className="text-xs text-amber-900/80 italic bg-amber-100/50 p-3 rounded-xl border border-amber-200">
          No policy rules executed for this turn. (Information queries do not fire deterministic rules engine evaluation).
        </p>
      ) : (
        <div className="space-y-3">
          {decisionTrace.map((item, idx) => (
            <div
              key={idx}
              className="bg-amber-100/80 border border-amber-300 rounded-2xl p-4 text-xs space-y-2 text-amber-950"
            >
              <div className="flex flex-wrap justify-between items-center gap-2">
                <span className="font-extrabold text-xs uppercase bg-amber-800 text-white px-2.5 py-0.5 rounded-full tracking-wide">
                  Rule: {item.rule}
                </span>
                {item.reason_code && (
                  <span className="font-bold text-[11px] bg-amber-200/90 text-amber-950 px-2.5 py-0.5 rounded-md border border-amber-400">
                    Reason Code: {item.reason_code}
                  </span>
                )}
              </div>

              <div>
                <span className="font-semibold text-amber-900/90 block mb-0.5">
                  Inputs:
                </span>
                <pre className="font-mono text-[11px] bg-amber-50/90 p-2 rounded-lg border border-amber-200 overflow-x-auto text-amber-950">
                  {JSON.stringify(item.inputs, null, 2)}
                </pre>
              </div>

              <div>
                <span className="font-semibold text-amber-900/90 block mb-0.5">
                  Outcome:
                </span>
                <div className="font-mono text-[11px] bg-amber-50/90 p-2 rounded-lg border border-amber-200 text-amber-950">
                  {typeof item.outcome === "object"
                    ? JSON.stringify(item.outcome, null, 2)
                    : String(item.outcome)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
