import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Airline Disruption Resolution Agent",
  description: "Customer-facing Airline Disruption Resolution Portal",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased bg-background text-main-text">
        {children}
      </body>
    </html>
  );
}
