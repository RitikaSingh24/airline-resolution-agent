"use client";

import React from "react";

interface MobileTabBarProps {
  activeView: "chat" | "bookings" | "actions" | "escalations";
  onViewChange: (view: "chat" | "bookings" | "actions" | "escalations") => void;
  actionsCount: number;
}

export const MobileTabBar: React.FC<MobileTabBarProps> = ({
  activeView,
  onViewChange,
  actionsCount,
}) => {
  const tabs = [
    { id: "chat" as const, label: "Chat", icon: "💬" },
    { id: "bookings" as const, label: "Bookings", icon: "✈️" },
    { id: "actions" as const, label: "Actions", icon: "📋", badge: actionsCount },
    { id: "escalations" as const, label: "Escalations", icon: "⚠️" },
  ];

  return (
    <nav
      className="lg:hidden flex-shrink-0 border-t border-border/20 bg-surface sticky bottom-0"
      aria-label="Mobile navigation"
    >
      <div className="flex">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onViewChange(tab.id)}
            aria-current={activeView === tab.id ? "page" : undefined}
            className={`flex-1 flex flex-col items-center justify-center py-2 min-h-[44px] transition-colors ${
              activeView === tab.id
                ? "text-primary border-t-2 border-primary"
                : "text-secondary-text"
            }`}
            style={{ paddingBottom: "max(0.5rem, env(safe-area-inset-bottom))" }}
          >
            <span className="text-xl mb-0.5">{tab.icon}</span>
            <span className="text-[10px] font-medium">{tab.label}</span>
            {tab.badge !== undefined && tab.badge > 0 && (
              <span className="absolute top-1 right-1/4 text-[10px] font-bold bg-primary text-white px-1.5 py-0.5 rounded-full">
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </div>
    </nav>
  );
};