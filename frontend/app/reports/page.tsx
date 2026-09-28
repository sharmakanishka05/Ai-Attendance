"use client";

import React, { useState, useEffect } from "react";
import {
  BarChart3,
  Download,
  Printer,
  Calendar,
  Filter,
  Users,
  CheckCircle2,
  FileSpreadsheet,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { StatCard } from "@/components/ui/StatCard";
import { api } from "@/lib/api";
import { AttendanceReportSummary, ClassModel } from "@/types";
import { downloadBlob } from "@/lib/utils";
import { useToast } from "@/components/ui/Toast";

export default function ReportsPage() {
  const { success, error } = useToast();
  const [report, setReport] = useState<AttendanceReportSummary | null>(null);
  const [classes, setClasses] = useState<ClassModel[]>([]);
  const [selectedClass, setSelectedClass] = useState<string>("all");
  const [selectedDays, setSelectedDays] = useState<number>(14);
  const [isExporting, setIsExporting] = useState(false);
  const [isExportingExcel, setIsExportingExcel] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadReport();
  }, [selectedClass, selectedDays]);

  const loadReport = async () => {
    setIsLoading(true);
    try {
      const [repData, clsData] = await Promise.all([
        api.getDashboardReport(selectedClass === "all" ? undefined : selectedClass, selectedDays),
        api.getClasses(),
      ]);
      setReport(repData);
      setClasses(clsData);
    } catch (err: any) {
      console.warn("Failed to load report data:", err);
      setReport({
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
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportCSV = async () => {
    setIsExporting(true);
    try {
      const blob = await api.downloadCSV(selectedClass);
      downloadBlob(blob, `kit_kanpur_attendance_report_${new Date().toISOString().split("T")[0]}.csv`);
      success("Attendance CSV report downloaded successfully!");
    } catch (err: any) {
      error(err.message || "Failed to download attendance CSV report.");
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportExcel = async () => {
    setIsExportingExcel(true);
    try {
      const blob = await api.downloadExcel(selectedClass);
      downloadBlob(blob, `kit_kanpur_attendance_report_${new Date().toISOString().split("T")[0]}.xlsx`);
      success("Attendance Excel spreadsheet (.xlsx) exported successfully!");
    } catch (err: any) {
      error(err.message || "Failed to download Excel report.");
    } finally {
      setIsExportingExcel(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 text-left">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <h1 className="text-[24px] font-semibold text-primary-text tracking-tight">
            Attendance Reports
          </h1>
          <p className="text-[13.5px] text-secondary-text">
            Kanpur Institute of Technology (KIT Kanpur) — MCA Final Year attendance verification and audit exports.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="md"
            leftIcon={<Printer className="w-4 h-4" />}
            onClick={handlePrint}
          >
            Print Report
          </Button>

          <Button
            variant="outline"
            size="md"
            leftIcon={<Download className="w-4 h-4" />}
            isLoading={isExporting}
            onClick={handleExportCSV}
          >
            Export CSV
          </Button>

          <Button
            variant="primary"
            size="md"
            leftIcon={<FileSpreadsheet className="w-4 h-4" />}
            isLoading={isExportingExcel}
            onClick={handleExportExcel}
          >
            Export Excel (.xlsx)
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white border border-border rounded-card p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <label className="text-[11px] font-semibold text-secondary-text uppercase block mb-1">
              Class Roster
            </label>
            <select
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
              className="h-9 px-3 text-[13px] bg-white border border-border rounded-control focus:outline-none focus:border-accent cursor-pointer"
            >
              <option value="all">All Enrolled Classes</option>
              {classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} — {c.section}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[11px] font-semibold text-secondary-text uppercase block mb-1">
              Time Horizon
            </label>
            <select
              value={selectedDays}
              onChange={(e) => setSelectedDays(Number(e.target.value))}
              className="h-9 px-3 text-[13px] bg-white border border-border rounded-control focus:outline-none focus:border-accent cursor-pointer"
            >
              <option value={7}>Last 7 Days</option>
              <option value={14}>Last 14 Days</option>
              <option value={30}>Last 30 Days</option>
            </select>
          </div>
        </div>

        <div className="text-[12px] text-secondary-text pt-3 sm:pt-0">
          Total verified records: <strong>{report?.total_records ?? 0}</strong>
        </div>
      </div>

      {/* Summary Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
        <StatCard
          label="Overall Attendance Rate"
          value={`${report?.attendance_rate ?? 0}%`}
          subtext="Verified student presence"
        />
        <StatCard
          label="Total Present"
          value={report?.present_count ?? 0}
          subtext="On-time attendance"
        />
        <StatCard
          label="Total Late"
          value={report?.late_count ?? 0}
          subtext="Excused with notice"
        />
        <StatCard
          label="Total Absent"
          value={report?.absent_count ?? 0}
          subtext="Unexcused absentees"
        />
      </div>

      {/* Class Comparison Section */}
      <div className="bg-white border border-border rounded-card p-5">
        <h3 className="text-[15px] font-semibold text-primary-text mb-1">
          Class Attendance Breakdown
        </h3>
        <p className="text-[12px] text-secondary-text mb-4">
          Live calculated attendance rates across enrolled sections
        </p>

        <div className="space-y-3">
          {(report?.class_comparisons || []).length === 0 ? (
            <div className="p-6 text-center text-[13px] text-secondary-text">
              No class comparison data available.
            </div>
          ) : (
            (report?.class_comparisons || []).map((comp) => (
              <div
                key={comp.class_id}
                className="p-3 border border-border rounded-control hover:bg-subtle/50 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="font-semibold text-[13.5px] text-primary-text">
                      {comp.name}
                    </span>
                    <span className="text-[12px] text-secondary-text ml-2">
                      ({comp.student_count ?? 0} students)
                    </span>
                  </div>
                  <span className="font-mono text-[13px] font-semibold text-primary-text">
                    {comp.attendance_rate}%
                  </span>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-subtle h-2 rounded-full overflow-hidden border border-border">
                  <div
                    className="bg-accent h-full rounded-full transition-all duration-300"
                    style={{ width: `${Math.min(comp.attendance_rate, 100)}%` }}
                  />
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
