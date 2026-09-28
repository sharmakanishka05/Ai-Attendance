"use client";

import React, { useState, useEffect } from "react";
import { BookOpen, Plus, Users, Clock, Calendar, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { api } from "@/lib/api";
import { ClassModel } from "@/types";
import { useToast } from "@/components/ui/Toast";

export default function ClassesPage() {
  const { success, error } = useToast();
  const [classes, setClasses] = useState<ClassModel[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  // Form State
  const [name, setName] = useState("");
  const [course, setCourse] = useState("");
  const [section, setSection] = useState("");
  const [teacherName, setTeacherName] = useState("Ajeet Singh");
  const [schedule, setSchedule] = useState("");

  useEffect(() => {
    loadClasses();
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("attendai_user");
      if (stored) {
        try {
          const u = JSON.parse(stored);
          if (u.full_name) setTeacherName(u.full_name);
        } catch {}
      }
    }
  }, []);

  const loadClasses = async () => {
    setIsLoading(true);
    try {
      const data = await api.getClasses();
      setClasses(data);
    } catch (err: any) {
      console.warn("Failed to load classes:", err);
      setClasses([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateClass = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !course.trim() || !section.trim()) {
      error("Please fill in the class name, course, and section.");
      return;
    }

    try {
      await api.createClass({
        name: name.trim(),
        course: course.trim(),
        section: section.trim(),
        teacher_name: teacherName.trim(),
        schedule: schedule.trim() || "Mon, Wed, Fri 09:00 AM",
      });
      success(`Class ${name} created successfully!`);
      setIsCreateModalOpen(false);
      setName("");
      setCourse("");
      setSection("");
      setSchedule("");
      loadClasses();
    } catch (err: any) {
      error(err.message || "Failed to create class.");
    }
  };

  return (
    <div className="space-y-6 text-left">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <h1 className="text-[24px] font-semibold text-primary-text tracking-tight">
            Class Management
          </h1>
          <p className="text-[13.5px] text-secondary-text">
            Manage course rosters, schedules, sections, and assigned teachers.
          </p>
        </div>

        <Button
          variant="primary"
          size="md"
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => setIsCreateModalOpen(true)}
        >
          Add Class
        </Button>
      </div>

      {/* Classes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {classes.map((cls) => (
          <div
            key={cls.id}
            className="bg-white border border-border rounded-card p-5 hover:border-border-hover transition-all duration-150 flex flex-col justify-between"
          >
            <div>
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className="text-[11px] font-semibold tracking-wider text-accent uppercase px-2 py-0.5 bg-accent-subtle rounded border border-accent/20">
                  {cls.course}
                </span>
                <span className="text-[12px] text-secondary-text font-mono">
                  {cls.section}
                </span>
              </div>

              <h3 className="text-[16px] font-semibold text-primary-text mt-1">
                {cls.name}
              </h3>

              <div className="mt-4 space-y-2 text-[13px] text-secondary-text">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-secondary-text" />
                  <span>
                    <strong>{cls.student_count ?? 3}</strong> enrolled students
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-secondary-text" />
                  <span>{cls.schedule || "Mon, Wed, Fri 09:00 AM"}</span>
                </div>

                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-full bg-subtle text-secondary-text flex items-center justify-center text-[9px] font-semibold border">
                    {cls.teacher_name.charAt(0)}
                  </div>
                  <span>Instructor: {cls.teacher_name}</span>
                </div>
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-border flex items-center justify-between">
              <span className="text-[12px] text-success flex items-center gap-1 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Active Roster
              </span>
              <a href="/attendance">
                <Button variant="outline" size="sm">
                  Start Session
                </Button>
              </a>
            </div>
          </div>
        ))}
      </div>

      {/* Modal: Create Class */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Add New Class"
        description="Create a new class roster and assign schedule."
        maxWidth="sm"
      >
        <form onSubmit={handleCreateClass} className="space-y-4 text-left">
          <Input
            label="Class / Subject Name"
            placeholder="e.g. Computer Science"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Course / Degree"
              placeholder="e.g. BCA, B.Tech"
              value={course}
              onChange={(e) => setCourse(e.target.value)}
              required
            />
            <Input
              label="Section"
              placeholder="e.g. Section A"
              value={section}
              onChange={(e) => setSection(e.target.value)}
              required
            />
          </div>

          <Input
            label="Schedule"
            placeholder="e.g. Mon, Wed, Fri 09:00 AM"
            value={schedule}
            onChange={(e) => setSchedule(e.target.value)}
          />

          <Input
            label="Teacher in Charge"
            value={teacherName}
            onChange={(e) => setTeacherName(e.target.value)}
          />

          <div className="flex justify-end gap-2 pt-3 border-t border-border">
            <Button
              variant="outline"
              size="sm"
              type="button"
              onClick={() => setIsCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit">
              Create Class
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
