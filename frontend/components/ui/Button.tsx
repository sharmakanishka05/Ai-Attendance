import React from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      isLoading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      "inline-flex items-center justify-center font-medium transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 disabled:pointer-events-none disabled:opacity-50 select-none";

    const variantStyles = {
      primary:
        "bg-accent text-white hover:bg-accent-hover shadow-sm active:translate-y-[0.5px]",
      secondary:
        "bg-subtle text-primary-text border border-border hover:bg-white hover:border-border-hover active:bg-subtle",
      outline:
        "border border-border bg-transparent text-primary-text hover:bg-subtle hover:border-border-hover",
      ghost:
        "text-secondary-text hover:text-primary-text hover:bg-subtle active:bg-border/40",
      danger:
        "bg-danger text-white hover:bg-red-700 shadow-sm active:translate-y-[0.5px]",
    };

    const sizeStyles = {
      sm: "h-8 px-3 text-[13px] rounded-control gap-1.5",
      md: "h-9 px-4 text-[14px] rounded-control gap-2",
      lg: "h-11 px-5 text-[15px] rounded-control gap-2.5",
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin text-current" />
        ) : (
          leftIcon
        )}
        <span>{children}</span>
        {!isLoading && rightIcon}
      </button>
    );
  }
);

Button.displayName = "Button";
