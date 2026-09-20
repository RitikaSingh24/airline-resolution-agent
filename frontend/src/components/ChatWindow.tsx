import React, { useEffect, useRef, useState } from "react";
import { ChatMessage } from "@/types";
import { MessageBubble } from "./MessageBubble";

interface ChatWindowProps {
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
  isSending: boolean;
  disabled?: boolean;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  onSendMessage,
  isSending,
  disabled = false,
}) => {
  const [inputText, setInputText] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isSending || disabled) return;
    onSendMessage(inputText);
    setInputText("");
  };

  return (
    <div className="bg-surface rounded-card border border-border/20 shadow-sm flex flex-col h-full min-h-0">
      {/* Header */}
      <div className="flex-shrink-0 flex justify-between items-center px-5 py-3 border-b border-border/15">
        <h2 className="text-sm font-semibold tracking-wider text-secondary-text uppercase">
          Agent Conversation Window
        </h2>
        {isSending && (
          <span className="text-xs font-semibold text-primary animate-pulse flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-primary animate-ping" />
            Processing policy resolution...
          </span>
        )}
      </div>

      {/* Messages List */}
      <div className="flex-1 min-h-0 overflow-y-auto px-4 py-3 space-y-1">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-secondary-text p-6 border-2 border-dashed border-border/20 rounded-2xl">
            <svg
              className="w-10 h-10 text-primary/40 mb-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            <p className="text-sm font-medium">No messages yet in this session.</p>
            <p className="text-xs text-secondary-text/70 mt-1">
              Select a quick-start scenario or type your inquiry below.
            </p>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Form */}
      <div className="flex-shrink-0 px-4 pb-4 pt-3 border-t border-border/15">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Type your flight disruption inquiry..."
            disabled={isSending || disabled}
            className="flex-1 min-w-0 bg-recessed text-main-text text-sm rounded-full px-5 py-3 border border-border/30 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all placeholder:text-secondary-text/60 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isSending || disabled}
            className="flex-shrink-0 bg-primary hover:bg-primary-hover text-white text-sm font-semibold rounded-full px-6 py-3 transition-all duration-150 active:scale-95 disabled:opacity-50 disabled:active:scale-100 shadow-md focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {isSending ? "Sending..." : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
};
