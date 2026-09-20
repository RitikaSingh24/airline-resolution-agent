"use client";

import React from "react";
import { Customer } from "@/types";

interface TopNavbarProps {
  activeView: string;
  selectedCustomer: Customer | null;
  conversationId: number | null;
  customerSelector: React.ReactNode;
  onMenuToggle: () => void;
  isMenuOpen: boolean;
}

export const TopNavbar: React.FC<TopNavbarProps> = ({
  activeView,
  selectedCustomer,
  conversationId,
  customerSelector,
  onMenuToggle,
  isMenuOpen,
}) => {
  const viewLabels: Record<string, string> = {
    chat: "Support chat",
    bookings: "My bookings",
    actions: "Actions log",
    escalations: "Escalations",
  };

  return (
    <header className="flex-shrink-0 h-14 bg-surface border-b border-border/20 flex items-center justify-between px-4 gap-3 min-w-0">
      {/* Left: Hamburger (mobile) + Logo */}
      <div className="flex items-center gap-2 min-w-0 shrink-0">
        <button
          className="lg:hidden p-1.5 rounded-lg hover:bg-recessed transition-colors flex-shrink-0"
          onClick={onMenuToggle}
          aria-label="Toggle navigation menu"
          aria-expanded={isMenuOpen}
        >
          <svg className="w-5 h-5 text-secondary-text" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <span className="w-2 h-2 rounded-full bg-primary flex-shrink-0" />
        <h1 className="text-sm font-black text-main-text tracking-tight truncate hidden sm:block">
          Airline Disruption Portal
        </h1>
        <h1 className="text-sm font-black text-main-text tracking-tight truncate sm:hidden">
          ADP
        </h1>
      </div>

      {/* Center: Breadcrumb */}
      <div className="hidden md:flex items-center flex-1 justify-center min-w-0">
        <span className="text-xs text-secondary-text truncate">
          {viewLabels[activeView] || activeView}
        </span>
      </div>

      {/* Right: Customer selector */}
      <div className="flex items-center gap-2 min-w-0 shrink-0">
        <div className="min-w-0 shrink-0">{customerSelector}</div>
      </div>
    </header>
  );
};