import React from "react";
import { cn } from "@/lib/utils";
import { Check, AlertTriangle, HelpCircle, Clock, X } from "lucide-react";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?:
    | "recognized"
    | "review"
    | "unknown"
    | "present"
    | "late"
    | "absent"
    | "active"
    | "completed"
    | "neutral";
  size?: "sm" | "md";
  showIcon?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = "neutral",
  size = "md",
  showIcon = true,
  children,
  ...props
}) => {
  const variantStyles = {
    recognized: "bg-success-subtle text-success border-success-border",
    review: "bg-warning-subtle text-warning border-warning-border",
    unknown: "bg-[#F3F4F6] text-secondary-text border-border",
    present: "bg-success-subtle text-success border-success-border",
    late: "bg-warning-subtle text-warning border-warning-border",
    absent: "bg-danger-subtle text-danger border-danger-border",
    active: "bg-blue-50 text-accent border-blue-200",
    completed: "bg-subtle text-secondary-text border-border",
    neutral: "bg-subtle text-secondary-text border-border",
  };

  const sizeStyles = {
    sm: "text-[11px] px-2 py-0.5 gap-1",
    md: "text-[12px] px-2.5 py-1 gap-1.5",
  };

  const renderIcon = () => {
    if (!showIcon) return null;
    const iconSize = size === "sm" ? "w-3 h-3" : "w-3.5 h-3.5";

    switch (variant) {
      case "recognized":
      case "present":
        return <Check className={iconSize} />;
      case "review":
      case "late":
        return <AlertTriangle className={iconSize} />;
      case "unknown":
        return <HelpCircle className={iconSize} />;
      case "absent":
        return <X className={iconSize} />;
      case "active":
        return <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />;
      default:
        return null;
    }
  };

  return (
    <span
      className={cn(
        "inline-flex items-center font-medium border rounded-full select-none",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {renderIcon()}
      <span>{children}</span>
    </span>
  );
};
