import React from "react";
import { cn } from "@/lib/utils";

export interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  subtext,
  trend,
  className,
}) => {
  return (
    <div
      className={cn(
        "bg-white border border-border rounded-card p-4 transition-all duration-150 text-left",
        className
      )}
    >
      <div className="text-[13px] font-medium text-secondary-text mb-1">
        {label}
      </div>
      <div className="text-[26px] font-semibold text-primary-text tracking-tight font-mono">
        {value}
      </div>
      {(subtext || trend) && (
        <div className="mt-1 flex items-center gap-1.5 text-[12px] text-secondary-text">
          {trend && (
            <span
              className={cn(
                "font-medium",
                trend.isPositive ? "text-success" : "text-danger"
              )}
            >
              {trend.isPositive ? "↑" : "↓"} {trend.value}
            </span>
          )}
          {subtext && <span>{subtext}</span>}
        </div>
      )}
    </div>
  );
};
