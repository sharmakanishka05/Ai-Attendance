import React from "react";
import { cn } from "@/lib/utils";
import { ChevronDown } from "lucide-react";

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options?: Array<{ label: string; value: string }>;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, options, children, id, ...props }, ref) => {
    const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

    return (
      <div className="w-full space-y-1.5 text-left">
        {label && (
          <label
            htmlFor={selectId}
            className="block text-[13px] font-medium text-primary-text"
          >
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          <select
            id={selectId}
            ref={ref}
            className={cn(
              "w-full h-9 bg-white text-primary-text text-[14px] border border-border rounded-control pl-3 pr-8 transition-colors duration-150 focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/10 disabled:bg-subtle disabled:text-muted-text disabled:cursor-not-allowed appearance-none cursor-pointer",
              error && "border-danger focus:border-danger focus:ring-danger/10",
              className
            )}
            {...props}
          >
            {options
              ? options.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))
              : children}
          </select>
          <ChevronDown className="absolute right-2.5 w-4 h-4 text-secondary-text pointer-events-none" />
        </div>
        {error && <p className="text-[12px] text-danger">{error}</p>}
      </div>
    );
  }
);

Select.displayName = "Select";
