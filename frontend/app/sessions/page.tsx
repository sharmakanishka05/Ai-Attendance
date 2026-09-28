"use client";

import React, { useState, useEffect } from "react";
import {
  CalendarCheck2,
  Clock,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  FileText,
  User,
  History,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";
import { AttendanceSession, AuditLogItem } from "@/types";
import { formatDate } from "@/lib/utils";

export default function SessionsPage() {
  const [sessions, setSessions] = useState<AttendanceSession[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [activeTab, setActiveTab] = useState<"sessions" | "audit">("sessions");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadSessionsAndAudit();
  }, []);

  const loadSessionsAndAudit = async () => {
    setIsLoading(true);
    try {
      const [sessData, auditData] = await Promise.all([
        api.getSessions(),
        api.getAuditLogs(),
      ]);
      setSessions(sessData);
      setAuditLogs(auditData);
    } catch (err: any) {
      console.warn("Failed to load sessions and audit data:", err);
      setSessions([]);
      setAuditLogs([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 text-left">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <h1 className="text-[24px] font-semibold text-primary-text tracking-tight">
            Sessions & Audit Logs
          </h1>
          <p className="text-[13.5px] text-secondary-text">
            Historical attendance sessions and immutable audit log for manual status corrections.
          </p>
        </div>

        {/* Tab switch */}
        <div className="flex items-center gap-1 p-1 bg-subtle border border-border rounded-control">
          <button
            onClick={() => setActiveTab("sessions")}
            className={`px-3 py-1.5 text-[13px] font-medium rounded-control transition-colors ${
              activeTab === "sessions"
                ? "bg-white text-primary-text shadow-sm"
                : "text-secondary-text hover:text-primary-text"
            }`}
          >
            Attendance Sessions ({sessions.length})
          </button>
          <button
            onClick={() => setActiveTab("audit")}
            className={`px-3 py-1.5 text-[13px] font-medium rounded-control transition-colors ${
              activeTab === "audit"
                ? "bg-white text-primary-text shadow-sm"
                : "text-secondary-text hover:text-primary-text"
            }`}
          >
            Audit Trail ({auditLogs.length})
          </button>
        </div>
      </div>

      {activeTab === "sessions" ? (
        <div className="bg-white border border-border rounded-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[13.5px] border-collapse">
              <thead>
                <tr className="bg-subtle/70 border-b border-border text-secondary-text text-[12px] font-medium">
                  <th className="py-3 px-4">Session Title</th>
                  <th className="py-3 px-4">Date & Time</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Breakdown</th>
                  <th className="py-3 px-4">Attendance Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {sessions.map((sess) => {
                  const totalMarked = sess.present_count + sess.late_count + sess.absent_count;
                  const rate =
                    totalMarked > 0
                      ? (
                          ((sess.present_count + sess.late_count) /
                            totalMarked) *
                          100.0
                        ).toFixed(1)
                      : "0.0";

                  return (
                    <tr key={sess.id} className="hover:bg-subtle/40 transition-colors">
                      <td className="py-3.5 px-4 font-semibold text-primary-text">
                        {sess.title}
                      </td>
                      <td className="py-3.5 px-4 text-secondary-text">
                        <div>{formatDate(sess.date)}</div>
                        <div className="text-[11px] font-mono">{sess.time}</div>
                      </td>
                      <td className="py-3.5 px-4">
                        <Badge
                          variant={sess.status === "completed" ? "completed" : "active"}
                          size="sm"
                        >
                          {sess.status.toUpperCase()}
                        </Badge>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-[12px]">
                        <span className="text-success font-semibold">
                          {sess.present_count}P
                        </span>{" "}
                        /{" "}
                        <span className="text-warning font-semibold">
                          {sess.late_count}L
                        </span>{" "}
                        /{" "}
                        <span className="text-danger font-semibold">
                          {sess.absent_count}A
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="font-mono font-medium text-primary-text">
                          {rate}%
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Audit Trail */
        <div className="bg-white border border-border rounded-card p-5 space-y-4">
          <div className="border-b border-border pb-3">
            <h3 className="text-[15px] font-semibold text-primary-text">
              Compliance & Correction Audit Logs
            </h3>
            <p className="text-[12.5px] text-secondary-text">
              All manual changes to attendance or biometric records are logged with immutable timestamps.
            </p>
          </div>

          <div className="space-y-3">
            {auditLogs.map((log) => (
              <div
                key={log.id}
                className="p-3.5 bg-subtle/60 border border-border rounded-control flex items-start gap-3 text-[13px]"
              >
                <div className="w-8 h-8 rounded-full bg-accent-subtle text-accent flex items-center justify-center flex-shrink-0 mt-0.5">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-primary-text">
                      {log.action}
                    </span>
                    <span className="text-[11px] font-mono text-secondary-text">
                      {new Date(log.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                  <p className="text-secondary-text mt-1 leading-relaxed">
                    {log.details}
                  </p>
                  <div className="text-[11px] text-muted-text mt-1.5 flex items-center gap-1.5">
                    <User className="w-3 h-3" />
                    <span>Logged by: {log.user_name || "Authorized Staff"}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
