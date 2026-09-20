import React from "react";

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Service Error",
  message,
  onRetry,
}) => {
  return (
    <div className="bg-red-50 border border-red-200 text-red-900 rounded-card p-5 shadow-xs flex items-start justify-between gap-4 my-3">
      <div className="flex items-start gap-3">
        <svg
          className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <div>
          <h3 className="text-sm font-bold text-red-950">{title}</h3>
          <p className="text-xs text-red-900 mt-1 leading-relaxed">{message}</p>
        </div>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="bg-red-700 hover:bg-red-800 text-white text-xs font-semibold px-4 py-2 rounded-full transition-all active:scale-95 flex-shrink-0"
        >
          Retry
        </button>
      )}
    </div>
  );
};
