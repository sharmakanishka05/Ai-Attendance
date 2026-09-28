"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Users,
  Camera,
  CalendarCheck2,
  TrendingUp,
  Clock,
  CheckCircle2,
  ArrowRight,
  BookOpen,
} from "lucide-react";
import { StatCard } from "@/components/ui/StatCard";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { api } from "@/lib/api";
import { AttendanceReportSummary, ClassModel, AuditLogItem } from "@/types";

export default function DashboardPage() {
  const [summary, setSummary] = useState<AttendanceReportSummary | null>(null);
  const [classes, setClasses] = useState<ClassModel[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [userName, setUserName] = useState("Ajeet");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("attendai_user");
      if (stored) {
        try {
          const u = JSON.parse(stored);
          if (u.full_name) {
            setUserName(u.full_name.split(" ")[0]);
          }
        } catch {}
      }
    }
  }, []);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      const [repData, clsData, logsData] = await Promise.all([
        api.getDashboardReport(),
        api.getClasses(),
        api.getAuditLogs(6).catch(() => []),
      ]);
      setSummary(repData);
      setClasses(clsData);
      setAuditLogs(logsData);
    } catch (err) {
      console.warn("Error loading dashboard data:", err);
      setSummary({
        attendance_rate: 0.0,
        present_count: 0,
        absent_count: 0,
        late_count: 0,
        total_records: 0,
        classes_today: 0,
        trend: [],
        class_comparisons: [],
      });
      setClasses([]);
      setAuditLogs([]);
    } finally {
      setIsLoading(false);
    }
  };

  const trendData = summary?.trend || [];
  const minRate = trendData.length > 0 ? Math.min(...trendData.map((d) => d.rate)) : 0;
  const maxRate = trendData.length > 0 ? Math.max(...trendData.map((d) => d.rate), 100) : 100;

  const todayFormatted = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="space-y-7 text-left">
      {/* Calm Header */}
      <div className="flex flex-wrap items-start justify-between gap-4 pb-1">
        <div>
          <div className="text-[13px] text-secondary-text font-medium">
            {todayFormatted}
          </div>
          <h1 className="text-[28px] font-semibold text-primary-text tracking-tight mt-0.5">
            Good morning, {userName}
          </h1>
          <p className="text-[14px] text-secondary-text mt-1">
            Kanpur Institute of Technology • MCA Final Year Attendance Overview
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link href="/attendance">
            <Button
              variant="primary"
              size="md"
              leftIcon={<Camera className="w-4 h-4" />}
            >
              Take Attendance
            </Button>
          </Link>
          <Link href="/reports">
            <Button variant="secondary" size="md">
              View Reports
            </Button>
          </Link>
        </div>
      </div>

      {/* Summary Metrics Section (Clean, calm, tabular nums) */}
      <div>
        <div className="text-[12px] font-semibold text-muted-text uppercase tracking-wider mb-2.5">
          Overall Metrics
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
          <StatCard
            label="Attendance Rate"
            value={`${summary?.attendance_rate ?? 0}%`}
            trend={{
              value: summary?.total_records ? `${summary.total_records} records verified` : "Live DB",
              isPositive: (summary?.attendance_rate ?? 0) >= 75,
            }}
          />
          <StatCard
            label="Present"
            value={summary?.present_count ?? 0}
            subtext="Sessions on-time"
          />
          <StatCard
            label="Late"
            value={summary?.late_count ?? 0}
            subtext="Excused with notice"
          />
          <StatCard
            label="Absent"
            value={summary?.absent_count ?? 0}
            subtext="Unexcused absentees"
          />
          <StatCard
            label="Classes Today"
            value={summary?.classes_today ?? 0}
            subtext={classes.length > 0 ? `${classes[0].name}` : "No classes"}
          />
        </div>
      </div>

      {/* 14-Day Attendance Trend Chart */}
      <div className="bg-white border border-border rounded-card p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-[15px] font-semibold text-primary-text">
              Attendance Trend (Last 14 Days)
            </h3>
            <p className="text-[12px] text-secondary-text">
              Live calculated session presence percentage from database records
            </p>
          </div>
          <div className="flex items-center gap-1.5 text-[12px] text-secondary-text">
            <span className="w-2.5 h-0.5 bg-accent rounded" />
            <span>Attendance Rate (%)</span>
          </div>
        </div>

        {/* Clean SVG Line Chart */}
        <div className="h-44 w-full relative">
          {trendData.length === 0 ? (
            <div className="h-full flex items-center justify-center text-[13px] text-secondary-text">
              No session data available for the trend chart.
            </div>
          ) : (
            <>
              <svg
                className="w-full h-full overflow-visible"
                viewBox={`0 0 ${Math.max(trendData.length - 1, 1) * 60} 100`}
                preserveAspectRatio="none"
              >
                {/* Horizontal Grid lines */}
                {[25, 50, 75].map((y) => (
                  <line
                    key={y}
                    x1="0"
                    y1={y}
                    x2={Math.max(trendData.length - 1, 1) * 60}
                    y2={y}
                    stroke="#E7E7E3"
                    strokeDasharray="3 3"
                    strokeWidth="1"
                  />
                ))}

                {/* Sparkline path */}
                {trendData.length > 1 && (
                  <polyline
                    fill="none"
                    stroke="#3157D5"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    points={trendData
                      .map((d, i) => {
                        const range = Math.max(maxRate - minRate, 1);
                        const normY = 100 - ((d.rate - minRate) / range) * 80 - 10;
                        return `${i * 60},${normY}`;
                      })
                      .join(" ")}
                  />
                )}

                {/* Data points */}
                {trendData.map((d, i) => {
                  const range = Math.max(maxRate - minRate, 1);
                  const normY = 100 - ((d.rate - minRate) / range) * 80 - 10;
                  return (
                    <circle
                      key={i}
                      cx={i * 60}
                      cy={normY}
                      r="3.5"
                      className="fill-white stroke-accent stroke-2 hover:r-5 transition-all cursor-pointer"
                    >
                      <title>{`${d.label}: ${d.rate}% (${d.present} present, ${d.absent} absent)`}</title>
                    </circle>
                  );
                })}
              </svg>

              {/* X Axis Labels */}
              <div className="flex justify-between text-[11px] text-secondary-text mt-2 font-mono">
                {trendData.map((d, i) => (
                  <span key={i} className={i % 2 === 0 ? "block" : "hidden sm:block"}>
                    {d.label}
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Two Column Layout: Today's Classes & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Today's Classes */}
        <div className="bg-white border border-border rounded-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-[15px] font-semibold text-primary-text">
              Assigned Classes
            </h3>
            <Link
              href="/classes"
              className="text-[12px] text-accent hover:underline flex items-center gap-1 font-medium"
            >
              All Classes <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-3">
            {classes.length === 0 ? (
              <div className="p-6 text-center text-[13px] text-secondary-text">
                No classes registered in the system.
              </div>
            ) : (
              classes.map((cls) => (
                <div
                  key={cls.id}
                  className="p-3 bg-subtle/70 border border-border rounded-control flex items-center justify-between"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-[13.5px] text-primary-text">
                        {cls.name}
                      </span>
                      <Badge variant="completed" size="sm">
                        {cls.course}
                      </Badge>
                    </div>
                    <div className="text-[12px] text-secondary-text mt-0.5">
                      {cls.section} • {cls.schedule || "Mon-Fri 09:30 AM"} • {cls.student_count || 3} students • {cls.teacher_name}
                    </div>
                  </div>
                  <Link href={`/attendance?class_id=${cls.id}`}>
                    <Button size="sm" variant="outline">
                      Take Roll
                    </Button>
                  </Link>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white border border-border rounded-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-[15px] font-semibold text-primary-text">
              Recent Activity & Audit
            </h3>
            <Link
              href="/sessions"
              className="text-[12px] text-accent hover:underline flex items-center gap-1 font-medium"
            >
              Session Logs <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-3.5">
            {auditLogs.length === 0 ? (
              <div className="p-6 text-center text-[13px] text-secondary-text">
                No audit activity logged yet.
              </div>
            ) : (
              auditLogs.slice(0, 4).map((log) => (
                <div key={log.id} className="flex items-start gap-3">
                  <span className="text-[11px] font-mono text-secondary-text w-14 flex-shrink-0 pt-0.5">
                    {new Date(log.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                  <div className="flex-1">
                    <div className="text-[13px] text-primary-text font-medium">
                      {log.action.replace(/_/g, " ")} • {log.user_name || "Ajeet Singh"}
                    </div>
                    <div className="text-[12px] text-secondary-text">
                      {log.details}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
