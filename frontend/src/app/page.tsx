"use client";

import React, { useState } from "react";
import { ActionsPanel } from "@/components/ActionsPanel";
import { AppShell } from "@/components/AppShell";
import { BookingCard } from "@/components/BookingCard";
import { ChatWindow } from "@/components/ChatWindow";
import { CustomerSelector } from "@/components/CustomerSelector";
import { DecisionTracePanel } from "@/components/DecisionTracePanel";
import { ErrorState } from "@/components/ErrorState";
import { EscalationBanner } from "@/components/EscalationBanner";
import { MobileDrawer } from "@/components/MobileDrawer";
import { MobileTabBar } from "@/components/MobileTabBar";
import { SidebarNav } from "@/components/SidebarNav";
import { TopNavbar } from "@/components/TopNavbar";
import { useChat } from "@/hooks/useChat";

export default function Home() {
  const {
    customers,
    selectedCustomer,
    bookings,
    conversationId,
    messages,
    actions,
    escalations,
    latestDecisionTrace,
    isLoading,
    isSending,
    error,
    selectCustomer,
    sendChatMessage,
    triggerScenario,
    retryInitialLoad,
  } = useChat();

  const [activeView, setActiveView] = useState<"chat" | "bookings" | "actions" | "escalations">("chat");
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <AppShell>
      {/* Top Navigation Bar */}
      <TopNavbar
        activeView={activeView}
        selectedCustomer={selectedCustomer}
        conversationId={conversationId}
        customerSelector={
          <CustomerSelector
            customers={customers}
            selectedCustomer={selectedCustomer}
            onSelectCustomer={selectCustomer}
            disabled={isLoading || isSending}
          />
        }
        onMenuToggle={() => setDrawerOpen(true)}
        isMenuOpen={drawerOpen}
      />

      {/* Mobile Slide-in Drawer */}
      <MobileDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        activeView={activeView}
        onViewChange={setActiveView}
        actionsCount={actions.length}
        onTriggerScenario={triggerScenario}
        isSending={isSending}
        isLoading={isLoading}
      />

      {/* Error Banner */}
      {error && (
        <div className="flex-shrink-0 px-4 py-2">
          <ErrorState
            message={error}
            onRetry={customers.length === 0 ? retryInitialLoad : undefined}
          />
        </div>
      )}

      {/* BODY: Sidebar + Workspace */}
      <div className="flex flex-1 min-h-0 overflow-hidden">

        {/* Desktop Sidebar — hidden on < lg */}
        <SidebarNav
          activeView={activeView}
          onViewChange={setActiveView}
          actionsCount={actions.length}
          onTriggerScenario={triggerScenario}
          isSending={isSending}
          isLoading={isLoading}
        />

        {/* Workspace — fills remaining width */}
        <main className="flex-1 min-w-0 flex flex-col min-h-0 overflow-hidden">

          {/* CHAT VIEW */}
          {activeView === "chat" && (
            <div className="flex-1 min-h-0 flex flex-col lg:flex-row overflow-hidden">

              {/* Chat Column */}
              <div className="flex-1 min-w-0 min-h-0 flex flex-col p-3 sm:p-4 gap-3 overflow-hidden">
                {escalations.length > 0 && (
                  <div className="flex-shrink-0">
                    <EscalationBanner escalations={escalations} />
                  </div>
                )}
                <div className="flex-1 min-h-0">
                  <ChatWindow
                    messages={messages}
                    onSendMessage={sendChatMessage}
                    isSending={isSending}
                    disabled={isLoading || !conversationId}
                  />
                </div>
              </div>

              {/* Context Panel — desktop lg+ */}
              <aside className="hidden lg:flex flex-col w-72 xl:w-80 shrink-0 border-l border-border/20 bg-surface overflow-y-auto p-3 gap-3">
                <DecisionTracePanel decisionTrace={latestDecisionTrace} />
              </aside>

              {/* Context Panel — mobile/tablet strip below chat */}
              <div className="lg:hidden flex-shrink-0 border-t border-border/20 bg-surface overflow-y-auto max-h-48 p-3 flex flex-col gap-3">
                <DecisionTracePanel decisionTrace={latestDecisionTrace} />
              </div>
            </div>
          )}

          {/* BOOKINGS VIEW */}
          {activeView === "bookings" && (
            <div className="flex-1 overflow-y-auto p-3 sm:p-4">
              <BookingCard
                bookings={bookings}
                customerName={selectedCustomer?.name}
              />
            </div>
          )}

          {/* ACTIONS VIEW */}
          {activeView === "actions" && (
            <div className="flex-1 overflow-y-auto p-3 sm:p-4">
              <ActionsPanel actions={actions} />
            </div>
          )}

          {/* ESCALATIONS VIEW */}
          {activeView === "escalations" && (
            <div className="flex-1 overflow-y-auto p-3 sm:p-4">
              {escalations.length > 0 ? (
                <EscalationBanner escalations={escalations} />
              ) : (
                <div className="bg-surface rounded-card p-5 border border-border/20 shadow-sm text-secondary-text text-sm italic">
                  No escalations for this customer.
                </div>
              )}
            </div>
          )}

        </main>
      </div>

      {/* Mobile Bottom Tab Bar */}
      <MobileTabBar
        activeView={activeView}
        onViewChange={setActiveView}
        actionsCount={actions.length}
      />
    </AppShell>
  );
}

