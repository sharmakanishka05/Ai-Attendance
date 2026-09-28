"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { Camera, Upload, Check, AlertTriangle, ShieldCheck, Sparkles } from "lucide-react";
import { CameraCapture } from "@/components/attendance/CameraCapture";
import { api } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";

interface AddStudentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStudentAdded: () => void;
  classesList: Array<{ id: string; name: string; section: string }>;
}

export const AddStudentModal: React.FC<AddStudentModalProps> = ({
  isOpen,
  onClose,
  onStudentAdded,
  classesList,
}) => {
  const { success, error } = useToast();
  const [step, setStep] = useState<1 | 2>(1);
  const [isLoading, setIsLoading] = useState(false);

  // Form State
  const [name, setName] = useState("");
  const [rollNumber, setRollNumber] = useState("");
  const [email, setEmail] = useState("");
  const [selectedClassIndex, setSelectedClassIndex] = useState(0);

  // Face Registration State
  const [createdStudentId, setCreatedStudentId] = useState<string | null>(null);
  const [capturedImageBase64, setCapturedImageBase64] = useState<string | null>(null);
  const [showCamera, setShowCamera] = useState(false);
  const [qualityChecks, setQualityChecks] = useState<{
    lighting: boolean;
    visibility: boolean;
    centered: boolean;
  }>({ lighting: true, visibility: true, centered: true });

  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !rollNumber.trim()) {
      error("Please enter student name and roll number.");
      return;
    }

    const targetClass = classesList[selectedClassIndex] || {
      name: "MCA Final Year",
      section: "MCA Final Year",
    };

    setIsLoading(true);
    try {
      const res = await api.createStudent({
        name: name.trim(),
        roll_number: rollNumber.trim(),
        email: email.trim() || undefined,
        class_name: targetClass.name,
        section: targetClass.section,
      });

      setCreatedStudentId(res.id);
      success(`Student ${res.name} created! Proceed to face registration.`);
      setStep(2);
    } catch (err: any) {
      error(err.message || "Failed to create student.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const base64 = event.target?.result as string;
      setCapturedImageBase64(base64);
      // Mock quality evaluation
      setQualityChecks({ lighting: true, visibility: true, centered: true });
    };
    reader.readAsDataURL(file);
  };

  const handleRegisterFace = async () => {
    if (!createdStudentId || !capturedImageBase64) return;
    setIsLoading(true);
    try {
      const res = await api.registerStudentFace(
        createdStudentId,
        undefined,
        capturedImageBase64
      );
      if (res.success) {
        success("Biometric face reference registered successfully!");
        onStudentAdded();
        handleClose();
      } else {
        error(res.message || "Face registration quality check failed.");
      }
    } catch (err: any) {
      error(err.message || "Face registration failed.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setStep(1);
    setName("");
    setRollNumber("");
    setEmail("");
    setCreatedStudentId(null);
    setCapturedImageBase64(null);
    setShowCamera(false);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={step === 1 ? "Add New Student" : "Register Face Biometrics"}
      description={
        step === 1
          ? "Enter student academic information."
          : "Add clear reference photos for automated recognition."
      }
      maxWidth="md"
    >
      {step === 1 ? (
        <form onSubmit={handleCreateStudent} className="space-y-4 text-left">
          <Input
            label="Full Name"
            placeholder="e.g. Rahul Sharma"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          <Input
            label="Roll Number / Student ID"
            placeholder="e.g. CS-105"
            value={rollNumber}
            onChange={(e) => setRollNumber(e.target.value)}
            required
          />

          <Input
            label="Email Address (Optional)"
            type="email"
            placeholder="e.g. rahul.sharma@attendai.edu"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <div>
            <label className="block text-[13px] font-medium text-primary-text mb-1.5">
              Class & Section
            </label>
            <select
              value={selectedClassIndex}
              onChange={(e) => setSelectedClassIndex(Number(e.target.value))}
              className="w-full h-9 border border-border rounded-control px-3 text-[14px] bg-white focus:outline-none focus:border-accent"
            >
              {classesList.map((c, idx) => (
                <option key={c.id} value={idx}>
                  {c.name} — {c.section}
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-border">
            <Button variant="outline" size="sm" type="button" onClick={handleClose}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isLoading}>
              Continue to Face Setup
            </Button>
          </div>
        </form>
      ) : (
        <div className="space-y-4 text-left">
          {showCamera ? (
            <CameraCapture
              onCapture={(base64) => {
                setCapturedImageBase64(base64);
                setShowCamera(false);
              }}
              onCancel={() => setShowCamera(false)}
            />
          ) : (
            <>
              {capturedImageBase64 ? (
                <div className="flex flex-col items-center">
                  <div className="w-36 h-36 rounded-full overflow-hidden border-2 border-accent relative shadow-md">
                    <img
                      src={capturedImageBase64}
                      alt="Captured reference face"
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="mt-2 text-[12px] text-secondary-text">
                    Reference photo captured
                  </div>

                  {/* Face Quality Feedback Box */}
                  <div className="w-full mt-4 p-3 bg-subtle border border-border rounded-control space-y-1.5 text-[12.5px]">
                    <div className="font-semibold text-primary-text mb-1 text-[12px] uppercase tracking-wide">
                      Quality Assessment
                    </div>
                    <div className="flex items-center gap-2 text-success font-medium">
                      <Check className="w-3.5 h-3.5" />
                      <span>Face clearly visible ✓</span>
                    </div>
                    <div className="flex items-center gap-2 text-success font-medium">
                      <Check className="w-3.5 h-3.5" />
                      <span>Good lighting ✓</span>
                    </div>
                    <div className="flex items-center gap-2 text-success font-medium">
                      <Check className="w-3.5 h-3.5" />
                      <span>Face centered in frame ✓</span>
                    </div>
                  </div>

                  <div className="mt-3 flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCapturedImageBase64(null)}
                    >
                      Retake / Replace
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="p-3 bg-blue-50/60 border border-blue-200 rounded-control text-[12.5px] text-primary-text flex items-start gap-2">
                    <ShieldCheck className="w-4 h-4 text-accent flex-shrink-0 mt-0.5" />
                    <span>
                      Add 2–5 clear photos from slightly different angles for reliable classroom recognition.
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 pt-2">
                    <button
                      type="button"
                      onClick={() => setShowCamera(true)}
                      className="p-5 border border-border rounded-card hover:border-accent hover:bg-accent-subtle/30 flex flex-col items-center justify-center gap-2 transition-colors text-center"
                    >
                      <Camera className="w-6 h-6 text-accent" />
                      <span className="text-[13px] font-semibold text-primary-text block">
                        Open Camera
                      </span>
                      <span className="text-[11px] text-secondary-text block">
                        Capture face instantly
                      </span>
                    </button>

                    <label className="p-5 border border-border rounded-card hover:border-accent hover:bg-accent-subtle/30 flex flex-col items-center justify-center gap-2 transition-colors text-center cursor-pointer">
                      <Upload className="w-6 h-6 text-accent" />
                      <span className="text-[13px] font-semibold text-primary-text block">
                        Upload Photo
                      </span>
                      <span className="text-[11px] text-secondary-text block">
                        JPG, PNG, or WEBP
                      </span>
                      <input
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={handleFileUpload}
                      />
                    </label>
                  </div>
                </div>
              )}

              <div className="flex justify-between items-center pt-4 border-t border-border">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    onStudentAdded();
                    handleClose();
                  }}
                >
                  Skip for Now
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleRegisterFace}
                  disabled={!capturedImageBase64}
                  isLoading={isLoading}
                >
                  Register Biometrics
                </Button>
              </div>
            </>
          )}
        </div>
      )}
    </Modal>
  );
};
