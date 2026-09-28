"use client";

import React, { useState } from "react";
import { AttendanceItem, DetectedFace, Student } from "@/types";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Check, AlertTriangle, HelpCircle, Edit2, UserCheck, ShieldAlert } from "lucide-react";

interface AttendanceReviewProps {
  items: AttendanceItem[];
  unknownFaces: DetectedFace[];
  allStudents: Student[];
  onUpdateStatus: (studentId: string, newStatus: "present" | "absent" | "late", reason: string) => void;
  onAssignUnknown: (boxId: string, studentId: string, reason: string) => void;
  onDismissUnknown: (boxId: string) => void;
  onConfirm: () => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

export const AttendanceReview: React.FC<AttendanceReviewProps> = ({
  items,
  unknownFaces,
  allStudents,
  onUpdateStatus,
  onAssignUnknown,
  onDismissUnknown,
  onConfirm,
  onCancel,
  isSubmitting = false,
}) => {
  // Modal for changing status + reason
  const [editingItem, setEditingItem] = useState<AttendanceItem | null>(null);
  const [targetStatus, setTargetStatus] = useState<"present" | "absent" | "late">("present");
  const [correctionReason, setCorrectionReason] = useState("");

  // Modal for assigning unknown face
  const [assigningFace, setAssigningFace] = useState<DetectedFace | null>(null);
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [assignReason, setAssignReason] = useState("");

  const presentCount = items.filter((i) => i.status === "present").length;
  const lateCount = items.filter((i) => i.status === "late").length;
  const absentCount = items.filter((i) => i.status === "absent").length;
  const unknownCount = unknownFaces.length;

  const openEditModal = (item: AttendanceItem) => {
    setEditingItem(item);
    setTargetStatus(item.status);
    setCorrectionReason(item.correction_reason || "Manual verification by teacher");
  };

  const handleSaveCorrection = () => {
    if (!editingItem) return;
    onUpdateStatus(editingItem.student_id, targetStatus, correctionReason || "Manual status change");
    setEditingItem(null);
  };

  const handleSaveUnknownAssignment = () => {
    if (!assigningFace || !selectedStudentId) return;
    onAssignUnknown(
      assigningFace.box_id,
      selectedStudentId,
      assignReason || "Teacher verified unknown face in photograph"
    );
    setAssigningFace(null);
    setSelectedStudentId("");
    setAssignReason("");
  };

  return (
    <div className="bg-white border border-border rounded-card p-6 text-left">
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h2 className="text-[17px] font-semibold text-primary-text">
            Attendance Review
          </h2>
          <p className="text-[13px] text-secondary-text">
            Verify recognized students and adjust statuses before finalizing.
          </p>
        </div>

        {/* Quick count pills */}
        <div className="flex items-center gap-2 text-[12px]">
          <span className="px-2.5 py-1 bg-success-subtle text-success border border-success-border rounded-full font-medium">
            {presentCount} Present
          </span>
          {lateCount > 0 && (
            <span className="px-2.5 py-1 bg-warning-subtle text-warning border border-warning-border rounded-full font-medium">
              {lateCount} Late
            </span>
          )}
          {absentCount > 0 && (
            <span className="px-2.5 py-1 bg-danger-subtle text-danger border border-danger-border rounded-full font-medium">
              {absentCount} Absent
            </span>
          )}
          {unknownCount > 0 && (
            <span className="px-2.5 py-1 bg-subtle text-secondary-text border border-border rounded-full font-medium">
              {unknownCount} Unknown
            </span>
          )}
        </div>
      </div>

      {/* Unknown Faces Section if any */}
      {unknownFaces.length > 0 && (
        <div className="mt-4 p-4 bg-amber-50/60 border border-warning-border rounded-card">
          <div className="flex items-center gap-2 mb-2.5 text-warning font-semibold text-[13.5px]">
            <ShieldAlert className="w-4 h-4" />
            <span>Unknown or Unrecognized Faces ({unknownFaces.length})</span>
          </div>
          <p className="text-[12px] text-secondary-text mb-3">
            The AI detected faces that didn't meet the recognition threshold. You can manually assign them to enrolled students or dismiss them.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {unknownFaces.map((f, idx) => (
              <div
                key={f.box_id}
                className="bg-white border border-border rounded-control p-2.5 flex items-center justify-between gap-3 shadow-sm"
              >
                <div className="flex items-center gap-2.5">
                  {f.face_crop_base64 ? (
                    <img
                      src={f.face_crop_base64}
                      alt="Unknown face crop"
                      className="w-10 h-10 rounded-full object-cover border border-border"
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-subtle flex items-center justify-center text-secondary-text">
                      <HelpCircle className="w-5 h-5" />
                    </div>
                  )}
                  <div>
                    <span className="text-[12px] font-medium text-primary-text block">
                      Face #{idx + 1}
                    </span>
                    <span className="text-[11px] text-secondary-text">
                      Confidence: {(f.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-1.5">
                  <Button
                    size="sm"
                    variant="outline"
                    className="text-[11px] h-7 px-2"
                    onClick={() => {
                      setAssigningFace(f);
                      setSelectedStudentId("");
                      setAssignReason("Identified from classroom photo");
                    }}
                  >
                    Assign
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-[11px] h-7 px-2 text-secondary-text"
                    onClick={() => onDismissUnknown(f.box_id)}
                  >
                    Dismiss
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Review Table */}
      <div className="mt-5 overflow-x-auto">
        <table className="w-full text-left text-[13px] border-collapse">
          <thead>
            <tr className="border-b border-border text-secondary-text font-medium text-[12px]">
              <th className="py-2.5 px-3">Student</th>
              <th className="py-2.5 px-3">Roll Number</th>
              <th className="py-2.5 px-3">Confidence</th>
              <th className="py-2.5 px-3">Attendance Status</th>
              <th className="py-2.5 px-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {items.map((item) => (
              <tr
                key={item.student_id}
                className="hover:bg-subtle/50 transition-colors"
              >
                <td className="py-3 px-3">
                  <div className="flex items-center gap-2.5">
                    {item.face_crop_base64 ? (
                      <img
                        src={item.face_crop_base64}
                        alt={item.student_name}
                        className="w-8 h-8 rounded-full object-cover border border-border"
                      />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-accent-subtle text-accent flex items-center justify-center font-semibold text-[11px]">
                        {item.student_name.slice(0, 2).toUpperCase()}
                      </div>
                    )}
                    <div>
                      <span className="font-medium text-primary-text block">
                        {item.student_name}
                      </span>
                      {item.is_modified && (
                        <span className="text-[10px] text-accent font-medium">
                          Modified: {item.correction_reason}
                        </span>
                      )}
                    </div>
                  </div>
                </td>
                <td className="py-3 px-3 font-mono text-secondary-text">
                  {item.roll_number}
                </td>
                <td className="py-3 px-3">
                  <span className="font-medium tabular-nums text-primary-text">
                    {(item.confidence * 100).toFixed(1)}%
                  </span>
                </td>
                <td className="py-3 px-3">
                  <Badge variant={item.status}>{item.status.toUpperCase()}</Badge>
                </td>
                <td className="py-3 px-3 text-right">
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 text-[12px] text-secondary-text hover:text-primary-text"
                    leftIcon={<Edit2 className="w-3 h-3" />}
                    onClick={() => openEditModal(item)}
                  >
                    Edit
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Confirmation Actions Bar */}
      <div className="mt-6 pt-4 border-t border-border flex flex-wrap items-center justify-between gap-3">
        <div className="text-[12px] text-secondary-text">
          Once confirmed, records will be saved to the database and duplicate entries prevented.
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="md" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={onConfirm}
            isLoading={isSubmitting}
            leftIcon={<UserCheck className="w-4 h-4" />}
          >
            Confirm Attendance
          </Button>
        </div>
      </div>

      {/* Modal: Manual Status Correction */}
      <Modal
        isOpen={!!editingItem}
        onClose={() => setEditingItem(null)}
        title="Edit Student Attendance"
        description={`Update status for ${editingItem?.student_name} (${editingItem?.roll_number})`}
        maxWidth="sm"
      >
        <div className="space-y-4 text-left">
          <div>
            <label className="block text-[13px] font-medium text-primary-text mb-1.5">
              Attendance Status
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(["present", "late", "absent"] as const).map((st) => (
                <button
                  key={st}
                  type="button"
                  onClick={() => setTargetStatus(st)}
                  className={`py-2 text-[13px] font-medium rounded-control border text-center transition-colors capitalize ${
                    targetStatus === st
                      ? "border-accent bg-accent-subtle text-accent font-semibold"
                      : "border-border bg-white text-secondary-text hover:bg-subtle"
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          <div>
            <Input
              label="Reason for correction (Audit trail requirement)"
              placeholder="e.g. Student arrived 10 min late with note"
              value={correctionReason}
              onChange={(e) => setCorrectionReason(e.target.value)}
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setEditingItem(null)}
            >
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleSaveCorrection}>
              Save Correction
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal: Assign Unknown Face */}
      <Modal
        isOpen={!!assigningFace}
        onClose={() => setAssigningFace(null)}
        title="Assign Unknown Face"
        description="Select an enrolled student to link with this detected face"
        maxWidth="md"
      >
        <div className="space-y-4 text-left">
          {assigningFace?.face_crop_base64 && (
            <div className="flex items-center gap-3 p-3 bg-subtle rounded-control">
              <img
                src={assigningFace.face_crop_base64}
                alt="Crop"
                className="w-12 h-12 rounded-full object-cover border"
              />
              <div className="text-[13px]">
                <span className="font-semibold block text-primary-text">Detected Face</span>
                <span className="text-secondary-text">Confidence: {(assigningFace.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
          )}

          <div>
            <label className="block text-[13px] font-medium text-primary-text mb-1">
              Select Student
            </label>
            <select
              value={selectedStudentId}
              onChange={(e) => setSelectedStudentId(e.target.value)}
              className="w-full h-9 border border-border rounded-control px-3 text-[14px] bg-white focus:outline-none focus:border-accent"
            >
              <option value="">-- Choose enrolled student --</option>
              {allStudents.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.roll_number}) — {s.class_name}
                </option>
              ))}
            </select>
          </div>

          <Input
            label="Reason for assignment"
            placeholder="e.g. Verified visually from classroom photo"
            value={assignReason}
            onChange={(e) => setAssignReason(e.target.value)}
          />

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setAssigningFace(null)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleSaveUnknownAssignment}
              disabled={!selectedStudentId}
            >
              Confirm Assignment
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
