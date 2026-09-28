import React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, helperText, leftIcon, rightIcon, id, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

    return (
      <div className="w-full space-y-1.5 text-left">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-[13px] font-medium text-primary-text"
          >
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {leftIcon && (
            <div className="absolute left-3 text-secondary-text pointer-events-none flex items-center">
              {leftIcon}
            </div>
          )}
          <input
            id={inputId}
            ref={ref}
            className={cn(
              "w-full h-9 bg-white text-primary-text text-[14px] placeholder:text-muted-text border border-border rounded-control px-3 transition-colors duration-150 focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/10 disabled:bg-subtle disabled:text-muted-text disabled:cursor-not-allowed",
              leftIcon && "pl-9",
              rightIcon && "pr-9",
              error && "border-danger focus:border-danger focus:ring-danger/10",
              className
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3 text-secondary-text pointer-events-none flex items-center">
              {rightIcon}
            </div>
          )}
        </div>
        {error && <p className="text-[12px] text-danger">{error}</p>}
        {!error && helperText && (
          <p className="text-[12px] text-secondary-text">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
