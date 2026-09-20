"use client";

import React, { ReactNode } from "react";

interface AppShellProps {
  children: ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  return (
    <div
      className="flex flex-col bg-background overflow-hidden"
      style={{ height: "100dvh" }}
    >
      {children}
    </div>
  );
};