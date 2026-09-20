import React from "react";
import { Action } from "@/types";

interface ActionsPanelProps {
  actions: Action[];
}

export const ActionsPanel: React.FC<ActionsPanelProps> = ({ actions }) => {
  return (
    <div className="bg-surface rounded-card p-5 border border-border/20 shadow-sm">
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-sm font-semibold tracking-wider text-secondary-text uppercase">
          Audited Actions Panel
        </h2>
        <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300">
          {actions.length} Executed
        </span>
      </div>

      {actions.length === 0 ? (
        <div className="text-xs text-secondary-text italic bg-background p-4 rounded-xl border border-border/10">
          No resolution actions have been logged for this conversation yet.
        </div>
      ) : (
        <div className="space-y-2.5">
          {actions.map((act) => (
            <div
              key={act.id}
              className="bg-emerald-50 border border-emerald-300 text-emerald-900 p-3.5 rounded-2xl flex flex-col gap-1 shadow-xs"
            >
              <div className="flex justify-between items-center">
                <span className="font-bold text-xs tracking-wider uppercase bg-emerald-200/80 text-emerald-950 px-2.5 py-0.5 rounded-md">
                  Action: {act.action_type}
                </span>
                <span className="text-[10px] text-emerald-800 font-semibold">
                  Status: Logged
                </span>
              </div>
              <div className="text-xs mt-1 font-mono bg-emerald-100/60 p-2 rounded-lg border border-emerald-200 text-emerald-950 overflow-x-auto">
                {JSON.stringify(act.details_json, null, 2)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
