import React from "react";
import { ChatMessage } from "@/types";

interface MessageBubbleProps {
  message: ChatMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === "user";

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"} my-2`}>
      <div
        className={`max-w-[85%] sm:max-w-[75%] px-5 py-3.5 rounded-2xl shadow-xs text-sm leading-relaxed ${
          isUser
            ? "bg-primary text-white rounded-br-xs"
            : "bg-secondary-container text-on-secondary-container rounded-bl-xs border border-border/10"
        }`}
      >
        <div className="font-semibold text-xs mb-1 opacity-80">
          {isUser ? "You" : "Resolution Assistant"}
        </div>
        <div className="whitespace-pre-wrap font-normal">{message.content}</div>
        {message.timestamp && (
          <div
            className={`text-[10px] mt-1.5 text-right ${
              isUser ? "text-white/70" : "text-secondary-text"
            }`}
          >
            {message.timestamp}
          </div>
        )}
      </div>
    </div>
  );
};
