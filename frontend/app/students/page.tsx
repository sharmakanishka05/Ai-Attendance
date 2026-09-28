"use client";

import React, { useState, useEffect } from "react";
import {
  Users,
  Search,
  Plus,
  Filter,
  CheckCircle2,
  AlertCircle,
  MoreHorizontal,
  ChevronRight,
  ShieldCheck,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { AddStudentModal } from "@/components/students/AddStudentModal";
import { StudentDrawer } from "@/components/students/StudentDrawer";
import { api } from "@/lib/api";
import { Student, ClassModel } from "@/types";
import { useToast } from "@/components/ui/Toast";

export default function StudentsPage() {
  const { success, error } = useToast();
  const [students, setStudents] = useState<Student[]>([]);
  const [classes, setClasses] = useState<ClassModel[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [selectedClass, setSelectedClass] = useState("all");
  const [selectedSection, setSelectedSection] = useState("all");
  const [faceFilter, setFaceFilter] = useState<string>("all");

  // Modals & Drawers
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [stData, clsData] = await Promise.all([
        api.getStudents(),
        api.getClasses(),
      ]);
      setStudents(stData);
      setClasses(clsData);
    } catch (err: any) {
      console.warn("Failed to load live students data:", err);
      setStudents([]);
      setClasses([]);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredStudents = students.filter((s) => {
    if (search.trim()) {
      const q = search.toLowerCase();
      const matchName = s.name.toLowerCase().includes(q);
      const matchRoll = s.roll_number.toLowerCase().includes(q);
      if (!matchName && !matchRoll) return false;
    }
    if (selectedClass !== "all" && s.class_name !== selectedClass) return false;
    if (selectedSection !== "all" && s.section !== selectedSection) return false;
    if (faceFilter === "enrolled" && !s.has_face_data) return false;
    if (faceFilter === "pending" && s.has_face_data) return false;
    return true;
  });

  return (
    <div className="space-y-6 text-left">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <h1 className="text-[24px] font-semibold text-primary-text tracking-tight">
            Students Directory
          </h1>
          <p className="text-[13.5px] text-secondary-text">
            Manage student profiles, biometric reference photos, and attendance records.
          </p>
        </div>

        <Button
          variant="primary"
          size="md"
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => setIsAddModalOpen(true)}
        >
          Add Student
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white border border-border rounded-card p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3 flex-1 min-w-[280px]">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px] max-w-sm">
            <Search className="w-4 h-4 text-secondary-text absolute left-3 top-2.5 pointer-events-none" />
            <input
              type="text"
              placeholder="Search by name or roll number..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full h-9 pl-9 pr-3 text-[13.5px] bg-subtle border border-border rounded-control placeholder:text-muted-text focus:outline-none focus:border-accent focus:bg-white transition-colors"
            />
          </div>

          {/* Class Filter */}
          <select
            value={selectedClass}
            onChange={(e) => setSelectedClass(e.target.value)}
            className="h-9 px-3 text-[13px] bg-white border border-border rounded-control focus:outline-none focus:border-accent cursor-pointer"
          >
            <option value="all">All Classes</option>
            {classes.map((c) => (
              <option key={c.id} value={c.name}>
                {c.name}
              </option>
            ))}
          </select>

          {/* Section Filter */}
          <select
            value={selectedSection}
            onChange={(e) => setSelectedSection(e.target.value)}
            className="h-9 px-3 text-[13px] bg-white border border-border rounded-control focus:outline-none focus:border-accent cursor-pointer"
          >
            <option value="all">All Sections</option>
            <option value="Section A">Section A</option>
            <option value="Section B">Section B</option>
            <option value="Section 1">Section 1</option>
          </select>

          {/* Biometric Status Filter */}
          <select
            value={faceFilter}
            onChange={(e) => setFaceFilter(e.target.value)}
            className="h-9 px-3 text-[13px] bg-white border border-border rounded-control focus:outline-none focus:border-accent cursor-pointer"
          >
            <option value="all">All Face Statuses</option>
            <option value="enrolled">Biometrics Registered</option>
            <option value="pending">Registration Pending</option>
          </select>
        </div>

        <div className="text-[12px] text-secondary-text">
          Showing <strong>{filteredStudents.length}</strong> students
        </div>
      </div>

      {/* Students Data Table */}
      <div className="bg-white border border-border rounded-card overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-secondary-text text-[13.5px]">
            Loading student records...
          </div>
        ) : filteredStudents.length === 0 ? (
          <div className="p-12 text-center text-secondary-text space-y-3">
            <Users className="w-8 h-8 text-muted-text mx-auto" />
            <div className="font-semibold text-primary-text text-[15px]">
              No students match your filter criteria.
            </div>
            <p className="text-[13px] max-w-sm mx-auto">
              Try adjusting your search query or clear the selected filters.
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSearch("");
                setSelectedClass("all");
                setSelectedSection("all");
                setFaceFilter("all");
              }}
            >
              Reset Filters
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[13.5px] border-collapse">
              <thead>
                <tr className="bg-subtle/70 border-b border-border text-secondary-text text-[12px] font-medium">
                  <th className="py-3 px-4">Student</th>
                  <th className="py-3 px-4">Roll Number</th>
                  <th className="py-3 px-4">Class & Section</th>
                  <th className="py-3 px-4">Face Data</th>
                  <th className="py-3 px-4">Attendance</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filteredStudents.map((student) => (
                  <tr
                    key={student.id}
                    onClick={() => setSelectedStudentId(student.id)}
                    className="hover:bg-subtle/50 transition-colors cursor-pointer"
                  >
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-accent-subtle text-accent border border-accent/20 flex items-center justify-center font-semibold text-[11px]">
                          {student.name.slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <span className="font-semibold text-primary-text block leading-tight">
                            {student.name}
                          </span>
                          {student.email && (
                            <span className="text-[11px] text-secondary-text">
                              {student.email}
                            </span>
                          )}
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 px-4 font-mono text-secondary-text">
                      {student.roll_number}
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="text-primary-text block">
                        {student.class_name}
                      </span>
                      <span className="text-[11px] text-secondary-text">
                        {student.section}
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      {student.has_face_data ? (
                        <div className="flex items-center gap-1.5 text-success text-[12px]">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Registered</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 text-muted-text text-[12px]">
                          <span className="w-2 h-2 rounded-full bg-muted-text" />
                          <span>Pending</span>
                        </div>
                      )}
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-subtle rounded-full h-1.5 overflow-hidden border border-border">
                          <div
                            className={`h-full rounded-full ${
                              student.attendance_rate >= 90
                                ? "bg-success"
                                : student.attendance_rate >= 75
                                ? "bg-warning"
                                : "bg-danger"
                            }`}
                            style={{ width: `${student.attendance_rate}%` }}
                          />
                        </div>
                        <span className="font-mono text-[12px] font-medium text-primary-text">
                          {student.attendance_rate}%
                        </span>
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <Badge
                        variant={student.status === "active" ? "active" : "neutral"}
                        size="sm"
                      >
                        {student.status.toUpperCase()}
                      </Badge>
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <span className="text-secondary-text hover:text-primary-text inline-flex p-1">
                        <ChevronRight className="w-4 h-4" />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Student Flow Modal */}
      <AddStudentModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onStudentAdded={loadData}
        classesList={classes.map((c) => ({ id: c.id, name: c.name, section: c.section }))}
      />

      {/* Student Detail Slide-over Drawer */}
      <StudentDrawer
        studentId={selectedStudentId}
        isOpen={!!selectedStudentId}
        onClose={() => setSelectedStudentId(null)}
        onDataChanged={loadData}
      />
    </div>
  );
}
