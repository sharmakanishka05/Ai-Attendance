"use client";

import React, { useState } from "react";
import { usePathname } from "next/navigation";
import { Search, Bell, Menu } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface TopBarProps {
  onOpenMobile: () => void;
}

const pageTitles: Record<string, { title: string; subtitle?: string }> = {
  "/": { title: "Overview", subtitle: "Here's what's happening with attendance today." },
  "/attendance": { title: "Attendance", subtitle: "Take attendance using camera or upload a classroom photo." },
  "/students": { title: "Students", subtitle: "Directory of registered students and face biometric data." },
  "/classes": { title: "Classes", subtitle: "Manage courses, sections, schedules, and enrollments." },
  "/reports": { title: "Reports", subtitle: "Analyze attendance trends, class breakdowns, and export records." },
  "/sessions": { title: "Sessions & Audit", subtitle: "Review attendance sessions and manual correction audit logs." },
  "/settings": { title: "Settings", subtitle: "Configure recognition threshold, camera preferences, and privacy controls." },
};

export const TopBar: React.FC<TopBarProps> = ({ onOpenMobile }) => {
  const pathname = usePathname();
  const [showNotifications, setShowNotifications] = useState(false);
  const [userName, setUserName] = useState("Ajeet Singh");
  const info = pageTitles[pathname] || { title: "KIT Kanpur" };

  React.useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("attendai_user");
      if (stored) {
        try {
          const u = JSON.parse(stored);
          if (u.full_name) setUserName(u.full_name);
        } catch {}
      }
    }
  }, []);

  const initials = userName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <header className="h-16 border-b border-border bg-white px-6 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobile}
          className="md:hidden p-2 rounded-control text-secondary-text hover:text-primary-text hover:bg-subtle"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-[17px] font-semibold text-primary-text tracking-tight text-left">
            {info.title}
          </h1>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Subtle quick search */}
        <div className="hidden sm:flex items-center relative w-56">
          <Search className="w-4 h-4 text-secondary-text absolute left-2.5 pointer-events-none" />
          <input
            type="text"
            placeholder="Search students, classes..."
            className="w-full h-8 pl-8 pr-3 text-[13px] bg-subtle border border-border rounded-control placeholder:text-muted-text focus:outline-none focus:border-accent focus:bg-white transition-colors"
          />
        </div>

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 rounded-control text-secondary-text hover:text-primary-text hover:bg-subtle relative transition-colors"
            aria-label="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-accent" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-72 bg-white border border-border rounded-card shadow-lg p-3 z-50 text-left animate-in fade-in duration-100">
              <div className="text-[12px] font-semibold text-primary-text mb-2">
                Recent Notifications
              </div>
              <div className="space-y-2 text-[12px] text-secondary-text">
                <div className="p-2 bg-subtle rounded-control">
                  <span className="font-medium text-primary-text block">Session Confirmed</span>
                  MCA Final Year attendance session verified.
                </div>
                <div className="p-2 bg-subtle rounded-control">
                  <span className="font-medium text-primary-text block">Threshold Active</span>
                  Face recognition running with 70% match threshold.
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User Pill */}
        <div className="hidden lg:flex items-center gap-2 pl-2 border-l border-border">
          <div className="w-7 h-7 rounded-full bg-accent text-white flex items-center justify-center text-[11px] font-semibold">
            {initials}
          </div>
          <span className="text-[13px] font-medium text-primary-text">
            {userName}
          </span>
        </div>
      </div>
    </header>
  );
};
