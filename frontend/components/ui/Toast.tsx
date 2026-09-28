"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  toast: (message: string, type?: ToastType) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((message: string, type: ToastType = "info") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider
      value={{
        toast: addToast,
        success: (msg) => addToast(msg, "success"),
        error: (msg) => addToast(msg, "error"),
        info: (msg) => addToast(msg, "info"),
      }}
    >
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none max-w-sm w-full">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "pointer-events-auto flex items-start gap-2.5 p-3.5 rounded-card border shadow-md transition-all duration-200 animate-in slide-in-from-bottom-2 bg-white text-left",
              t.type === "success" && "border-success-border",
              t.type === "error" && "border-danger-border",
              t.type === "info" && "border-border"
            )}
          >
            {t.type === "success" && (
              <CheckCircle2 className="w-4 h-4 text-success flex-shrink-0 mt-0.5" />
            )}
            {t.type === "error" && (
              <AlertCircle className="w-4 h-4 text-danger flex-shrink-0 mt-0.5" />
            )}
            {t.type === "info" && (
              <Info className="w-4 h-4 text-accent flex-shrink-0 mt-0.5" />
            )}
            <p className="text-[13px] text-primary-text flex-1 leading-snug">
              {t.message}
            </p>
            <button
              onClick={() => removeToast(t.id)}
              className="text-secondary-text hover:text-primary-text p-0.5"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
};
