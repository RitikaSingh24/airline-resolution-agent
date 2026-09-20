"use client";

import React from "react";
import { SCENARIO_INTENTS } from "@/lib/constants";

interface SidebarNavProps {
  activeView: "chat" | "bookings" | "actions" | "escalations";
  onViewChange: (view: "chat" | "bookings" | "actions" | "escalations") => void;
  actionsCount: number;
  onTriggerScenario: (text: string, customerId: number) => void;
  isSending: boolean;
  isLoading: boolean;
}

export const SidebarNav: React.FC<SidebarNavProps> = ({
  activeView,
  onViewChange,
  actionsCount,
  onTriggerScenario,
  isSending,
  isLoading,
}) => {
  const navItems = [
    { id: "chat" as const, label: "Support chat", icon: "💬" },
    { id: "bookings" as const, label: "My bookings", icon: "✈️" },
    { id: "actions" as const, label: "Actions log", icon: "📋", badge: actionsCount },
    { id: "escalations" as const, label: "Escalations", icon: "⚠️" },
  ];

  return (
    <nav
      className="hidden lg:flex w-48 xl:w-56 shrink-0 bg-surface border-r border-border/20 flex-col overflow-y-auto"
      aria-label="Main navigation"
    >
      {/* Main navigation items */}
      <div className="flex-1 pt-3 pb-2 space-y-0.5">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onViewChange(item.id)}
            aria-current={activeView === item.id ? "page" : undefined}
            className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm font-medium transition-colors min-h-[44px] ${
              activeView === item.id
                ? "bg-primary/10 text-primary border-r-2 border-primary"
                : "text-secondary-text hover:bg-recessed hover:text-main-text"
            }`}
          >
            <span className="text-base leading-none shrink-0">{item.icon}</span>
            <span className="flex-1 text-left truncate">{item.label}</span>
            {item.badge !== undefined && item.badge > 0 && (
              <span className="text-xs font-bold bg-primary text-white px-1.5 py-0.5 rounded-full shrink-0">
                {item.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Quick scenarios */}
      <div className="border-t border-border/20 p-3">
        <p className="text-[10px] font-semibold tracking-wider text-secondary-text uppercase mb-2 px-1">
          Quick scenarios
        </p>
        <div className="space-y-1.5">
          {SCENARIO_INTENTS.map((sc) => (
            <button
              key={sc.id}
              onClick={() => onTriggerScenario(sc.text, sc.customerId)}
              disabled={isSending || isLoading}
              className="w-full bg-background hover:bg-primary/10 border border-border/30 rounded-xl p-2.5 text-left transition-all duration-150 active:scale-95 group focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50 min-h-[52px]"
            >
              <span className="text-xs font-extrabold text-primary group-hover:text-primary-hover tracking-wide block truncate">
                {sc.label}
              </span>
              <p className="text-[10px] text-secondary-text leading-snug mt-0.5 line-clamp-2">
                {sc.description}
              </p>
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
};