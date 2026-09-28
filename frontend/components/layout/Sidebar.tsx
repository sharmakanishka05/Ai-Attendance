"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Camera,
  Users,
  BookOpen,
  BarChart3,
  CalendarCheck2,
  Settings,
  ShieldCheck,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { User } from "@/types";

const mainNav = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Attendance", href: "/attendance", icon: Camera },
  { name: "Students", href: "/students", icon: Users },
  { name: "Classes", href: "/classes", icon: BookOpen },
  { name: "Reports", href: "/reports", icon: BarChart3 },
];

const manageNav = [
  { name: "Sessions", href: "/sessions", icon: CalendarCheck2 },
  { name: "Settings", href: "/settings", icon: Settings },
];

export const Sidebar: React.FC<{ className?: string; onCloseMobile?: () => void }> = ({
  className,
  onCloseMobile,
}) => {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    // Load authenticated user info from localStorage or /auth/me
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("attendai_user");
      if (stored) {
        try {
          setUser(JSON.parse(stored));
        } catch {
          // ignore
        }
      }
    }
  }, []);

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {
      // ignore
    }
    if (typeof window !== "undefined") {
      localStorage.removeItem("attendai_user");
      document.cookie = "auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    }
    router.push("/login");
    router.refresh();
  };

  const displayName = user?.full_name || "Ajeet Singh";
  const displayRole = user?.role === "admin" ? "Faculty & Admin" : "Instructor";
  const initials = displayName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <aside
      className={cn(
        "w-[240px] flex-shrink-0 bg-white border-r border-border h-screen flex flex-col justify-between py-5 px-3 select-none text-left",
        className
      )}
    >
      <div>
        {/* Brand Header */}
        <div className="px-3 mb-6 flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-control bg-accent flex items-center justify-center text-white font-semibold text-sm shadow-sm">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <span className="text-[16px] font-semibold text-primary-text tracking-tight block leading-tight">
              KIT Kanpur
            </span>
            <span className="text-[11px] text-secondary-text block leading-none mt-0.5 font-normal">
              Attendance Portal
            </span>
          </div>
        </div>

        {/* Primary Navigation */}
        <nav className="space-y-0.5">
          {mainNav.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);
            const Icon = item.icon;

            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={onCloseMobile}
                className={cn(
                  "flex items-center gap-2.5 px-3 py-2 rounded-control text-[13.5px] font-medium transition-colors duration-150",
                  isActive
                    ? "bg-subtle text-accent font-semibold"
                    : "text-secondary-text hover:text-primary-text hover:bg-subtle/70"
                )}
              >
                <Icon
                  className={cn(
                    "w-4 h-4 transition-colors",
                    isActive ? "text-accent" : "text-secondary-text"
                  )}
                />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Manage Section */}
        <div className="mt-7">
          <div className="px-3 mb-1.5 text-[11px] font-semibold text-muted-text uppercase tracking-wider">
            Manage
          </div>
          <nav className="space-y-0.5">
            {manageNav.map((item) => {
              const isActive = pathname.startsWith(item.href);
              const Icon = item.icon;

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={onCloseMobile}
                  className={cn(
                    "flex items-center gap-2.5 px-3 py-2 rounded-control text-[13.5px] font-medium transition-colors duration-150",
                    isActive
                      ? "bg-subtle text-accent font-semibold"
                      : "text-secondary-text hover:text-primary-text hover:bg-subtle/70"
                  )}
                >
                  <Icon
                    className={cn(
                      "w-4 h-4 transition-colors",
                      isActive ? "text-accent" : "text-secondary-text"
                    )}
                  />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* User Profile Footer with Logout */}
      <div className="pt-4 border-t border-border/80 px-2 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <div className="w-8 h-8 rounded-full bg-accent-subtle text-accent border border-accent/20 flex items-center justify-center font-semibold text-[11.5px] flex-shrink-0">
            {initials}
          </div>
          <div className="overflow-hidden">
            <div className="text-[13px] font-medium text-primary-text truncate">
              {displayName}
            </div>
            <div className="text-[11px] text-secondary-text truncate">
              {displayRole}
            </div>
          </div>
        </div>

        <button
          onClick={handleLogout}
          aria-label="Sign out"
          title="Sign out"
          className="p-1.5 text-secondary-text hover:text-danger hover:bg-subtle rounded-control transition-colors"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
};
