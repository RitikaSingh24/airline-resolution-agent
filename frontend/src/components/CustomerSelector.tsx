import React from "react";
import { Customer } from "@/types";

interface CustomerSelectorProps {
  customers: Customer[];
  selectedCustomer: Customer | null;
  onSelectCustomer: (customer: Customer) => void;
  disabled?: boolean;
}

export const CustomerSelector: React.FC<CustomerSelectorProps> = ({
  customers,
  selectedCustomer,
  onSelectCustomer,
  disabled = false,
}) => {
  return (
    <div className="relative inline-flex items-center">
      <select
        aria-label="Select Customer Account"
        value={selectedCustomer?.id || ""}
        onChange={(e) => {
          const cust = customers.find((c) => c.id === Number(e.target.value));
          if (cust) onSelectCustomer(cust);
        }}
        disabled={disabled}
        className={`bg-background text-main-text text-xs font-semibold px-3 py-1.5 pr-8 rounded-full border border-border/30 hover:border-primary focus:outline-none focus:ring-2 focus:ring-primary appearance-none cursor-pointer transition-colors shadow-xs ${
          disabled ? "opacity-60 cursor-not-allowed" : ""
        }`}
      >
        {customers.map((cust) => (
          <option key={cust.id} value={cust.id} className="bg-surface text-main-text font-medium py-1">
            {cust.name} ({cust.tier})
          </option>
        ))}
      </select>
      <div className="pointer-events-none absolute right-2.5 flex items-center text-secondary-text">
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>
  );
};

