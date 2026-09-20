"use client";

import React, { useEffect } from "react";
import { SCENARIO_INTENTS } from "@/lib/constants";

interface MobileDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  activeView: "chat" | "bookings" | "actions" | "escalations";
  onViewChange: (view: "chat" | "bookings" | "actions" | "escalations") => void;
  actionsCount: number;
  onTriggerScenario: (text: string, customerId: number) => void;
  isSending: boolean;
  isLoading: boolean;
}

export const MobileDrawer: React.FC<MobileDrawerProps> = ({
  isOpen,
  onClose,
  activeView,
  onViewChange,
  actionsCount,
  onTriggerScenario,
  isSending,
  isLoading,
}) => {
  // Handle escape key to close drawer
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  // Lock body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  const navItems = [
    { id: "chat" as const, label: "Support chat", icon: "💬" },
    { id: "bookings" as const, label: "My bookings", icon: "✈️" },
    { id: "actions" as const, label: "Actions log", icon: "📋", badge: actionsCount },
    { id: "escalations" as const, label: "Escalations", icon: "⚠️" },
  ];

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[90] transition-opacity duration-200"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Drawer */}
      <div
        className={`fixed inset-y-0 left-0 h-full w-72 bg-surface text-main-text border-r border-border/20 z-[100] transform transition-transform duration-200 flex flex-col shadow-2xl overflow-y-auto ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        role="dialog"
        aria-modal="true"
        aria-label="Navigation menu"
      >
        {/* Drawer Header */}
        <div className="flex items-center justify-between px-4 py-3.5 border-b border-border/20 bg-surface flex-shrink-0">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-primary shrink-0" />
            <span className="font-bold text-sm text-main-text tracking-tight">Navigation Menu</span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-recessed text-secondary-text hover:text-main-text transition-colors"
            aria-label="Close menu"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Navigation items */}
        <div className="flex-1 py-3 space-y-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                onViewChange(item.id);
                onClose();
              }}
              aria-current={activeView === item.id ? "page" : undefined}
              className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium transition-colors ${
                activeView === item.id
                  ? "bg-primary/10 text-primary border-r-4 border-primary font-semibold"
                  : "text-secondary-text hover:bg-recessed hover:text-main-text"
              }`}
            >
              <span className="text-xl shrink-0">{item.icon}</span>
              <span className="flex-1 text-left">{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="text-xs font-bold bg-primary text-white px-2 py-0.5 rounded-full">
                  {item.badge}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Quick scenarios */}
        <div className="border-t border-border/20 p-4 bg-surface flex-shrink-0">
          <p className="text-xs font-semibold tracking-wider text-secondary-text uppercase mb-3">
            Quick scenarios
          </p>
          <div className="space-y-2">
            {SCENARIO_INTENTS.map((sc) => (
              <button
                key={sc.id}
                onClick={() => {
                  onTriggerScenario(sc.text, sc.customerId);
                  onClose();
                }}
                disabled={isSending || isLoading}
                className="w-full bg-background hover:bg-primary/10 border border-border/30 rounded-xl p-3 text-left transition-all duration-150 active:scale-95 group focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
              >
                <span className="text-xs font-extrabold text-primary group-hover:text-primary-hover tracking-wide block">
                  {sc.label}
                </span>
                <p className="text-[11px] text-secondary-text leading-snug mt-0.5">
                  {sc.description}
                </p>
              </button>
            ))}
          </div>
        </div>
      </div>
    </>
  );
};