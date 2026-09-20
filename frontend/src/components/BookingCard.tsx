import React from "react";
import { Booking } from "@/types";

interface BookingCardProps {
  bookings: Booking[];
  customerName?: string;
}

export const BookingCard: React.FC<BookingCardProps> = ({ bookings, customerName }) => {
  if (!bookings || bookings.length === 0) {
    return (
      <div className="bg-surface rounded-card p-5 border border-border/20 shadow-sm text-secondary-text text-sm italic">
        No booking records found for {customerName || "this customer"}.
      </div>
    );
  }

  const getStatusBadge = (status: string, delayMinutes?: number | null) => {
    const s = status.toLowerCase();
    if (s.includes("cancel")) {
      return "bg-red-100 text-red-900 border-red-300";
    }
    if (s.includes("delay") || (delayMinutes && delayMinutes > 0)) {
      return "bg-amber-100 text-amber-900 border-amber-300";
    }
    return "bg-emerald-100 text-emerald-900 border-emerald-300";
  };

  return (
    <div className="bg-surface rounded-card p-5 border border-border/20 shadow-sm">
      <h2 className="text-sm font-semibold tracking-wider text-secondary-text uppercase mb-3">
        Flight Bookings
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {bookings.map((b) => {
          const statusBadgeClass = getStatusBadge(b.status, b.delay_minutes);
          return (
            <div
              key={b.id}
              className="bg-background rounded-2xl p-4 border border-border/20 flex flex-col justify-between gap-3 shadow-xs"
            >
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-xs font-bold text-secondary-text tracking-wide uppercase">
                    PNR: {b.pnr} ({b.segment_label})
                  </span>
                  <h3 className="text-base font-bold text-main-text mt-0.5">
                    {b.flight_no || "Return Segment"} • {b.route}
                  </h3>
                </div>
                <span
                  className={`text-xs px-2.5 py-1 rounded-full font-bold border ${statusBadgeClass}`}
                >
                  {b.status}
                </span>
              </div>

              <div className="text-xs text-secondary-text grid grid-cols-2 gap-2 bg-recessed/40 p-2.5 rounded-xl border border-border/10">
                <div>
                  <span className="text-secondary-text/80 block">Date & Sched:</span>
                  <span className="font-semibold text-main-text">
                    {b.flight_date} @ {b.sched_dep}
                  </span>
                </div>
                {b.new_dep && (
                  <div>
                    <span className="text-secondary-text/80 block">New Dep:</span>
                    <span className="font-semibold text-amber-800">{b.new_dep}</span>
                  </div>
                )}
                {b.delay_minutes ? (
                  <div>
                    <span className="text-secondary-text/80 block">Delay:</span>
                    <span className="font-semibold text-amber-800">
                      {b.delay_minutes} mins ({(b.delay_minutes / 60).toFixed(1)}h)
                    </span>
                  </div>
                ) : null}
                {b.cause && (
                  <div className="col-span-2">
                    <span className="text-secondary-text/80 block">Cause:</span>
                    <span className="font-semibold text-main-text">{b.cause}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
