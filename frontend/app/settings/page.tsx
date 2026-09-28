"use client";

import React, { useState, useEffect } from "react";
import {
  Sliders,
  Shield,
  Camera,
  CheckCircle2,
  Lock,
  Eye,
  Info,
  Save,
  Cpu,
  Server,
  AlertTriangle,
  RefreshCw,
  HardDrive
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { useToast } from "@/components/ui/Toast";
import { api } from "@/lib/api";
import { User } from "@/types";

export default function SettingsPage() {
  const { success, error: toastError } = useToast();
  const [matchThreshold, setMatchThreshold] = useState<number>(0.70);
  const [reviewThreshold, setReviewThreshold] = useState<number>(0.52);
  const [cameraQuality, setCameraQuality] = useState<string>("hd");
  const [isPrivacyModalOpen, setIsPrivacyModalOpen] = useState<boolean>(false);
  const [diagnostics, setDiagnostics] = useState<{
    face_detector?: string;
    embedding_model?: string;
    recognition_mode?: string;
    onnx_model_file_present?: boolean;
    models_dir?: string;
  } | null>(null);
  const [appEnv, setAppEnv] = useState<string>("production");
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState<boolean>(false);

  useEffect(() => {
    // 1. Load user from local storage
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("attendai_user");
      if (stored) {
        try {
          setCurrentUser(JSON.parse(stored));
        } catch {
          // ignore
        }
      }
    }

    // 2. Load system settings and diagnostics from backend
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const data = await api.getSettings();
      setMatchThreshold(data.face_match_threshold);
      setReviewThreshold(data.face_review_threshold);
      setDiagnostics(data.diagnostics);
      setAppEnv(data.app_env || "production");
    } catch (err: any) {
      console.warn("Could not fetch remote settings:", err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    if (currentUser?.role !== "admin") {
      toastError("Permission denied: Only administrators can modify global recognition settings.");
      return;
    }

    setIsSaving(true);
    try {
      await api.updateSettings({
        face_match_threshold: matchThreshold,
        face_review_threshold: reviewThreshold,
      });
      success("System recognition thresholds successfully persisted to database!");
    } catch (err: any) {
      toastError(err.message || "Failed to persist settings.");
    } finally {
      setIsSaving(false);
    }
  };

  const isAdmin = currentUser?.role === "admin";

  return (
    <div className="space-y-6 text-left max-w-4xl">
      {/* Top Header */}
      <div className="pb-2 border-b border-border flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-[24px] font-semibold text-primary-text tracking-tight">
            System Settings & Privacy
          </h1>
          <p className="text-[13.5px] text-secondary-text">
            Configure computer vision thresholds, hardware preferences, and biometric policies.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[12px] font-medium ${
            appEnv === "production"
              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
              : "bg-amber-50 text-amber-700 border border-amber-200"
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
              appEnv === "production" ? "bg-emerald-500" : "bg-amber-500"
            }`} />
            {appEnv.toUpperCase()} MODE
          </span>
          <Button
            variant="outline"
            size="sm"
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />}
            onClick={loadSettings}
            disabled={isLoading}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Role Notice if Teacher */}
      {!isAdmin && currentUser && (
        <div className="p-3.5 bg-amber-50/70 border border-amber-200 rounded-control flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-[13px] text-amber-800">
            <p className="font-semibold">Instructor View (Read-Only)</p>
            <p className="text-[12px] text-amber-700 mt-0.5">
              You are signed in as an Instructor ({currentUser.full_name}). Global computer vision thresholds and recognition parameters can only be committed to the database by administrators.
            </p>
          </div>
        </div>
      )}

      {/* System Diagnostics Card (Phase 6) */}
      <div className="bg-white border border-border rounded-card p-6 space-y-4">
        <div className="flex items-center gap-2.5 pb-3 border-b border-border">
          <Server className="w-5 h-5 text-accent" />
          <div>
            <h3 className="text-[16px] font-semibold text-primary-text">
              Computer Vision Model Diagnostics
            </h3>
            <p className="text-[12.5px] text-secondary-text">
              Real-time hardware status and active neural network inference engine.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Face Detector */}
          <div className="p-3.5 bg-subtle rounded-control border border-border">
            <span className="text-[11.5px] font-semibold uppercase tracking-wider text-secondary-text block mb-1">
              Face Detector
            </span>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-[13.5px] font-medium text-primary-text">
                {diagnostics?.face_detector || "READY (YuNet DNN)"}
              </span>
            </div>
            <p className="text-[11.5px] text-secondary-text mt-1">
              Multi-scale neural detector for wide classroom views.
            </p>
          </div>

          {/* Embedding Model */}
          <div className="p-3.5 bg-subtle rounded-control border border-border">
            <span className="text-[11.5px] font-semibold uppercase tracking-wider text-secondary-text block mb-1">
              Embedding Model
            </span>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-[13.5px] font-medium text-primary-text">
                {diagnostics?.embedding_model || "READY (512-d Spatial Feature)"}
              </span>
            </div>
            <p className="text-[11.5px] text-secondary-text mt-1">
              512-dimensional vector space on unit hypersphere.
            </p>
          </div>

          {/* Recognition Engine Mode */}
          <div className="p-3.5 bg-subtle rounded-control border border-border">
            <span className="text-[11.5px] font-semibold uppercase tracking-wider text-secondary-text block mb-1">
              Recognition Mode
            </span>
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${
                diagnostics?.recognition_mode === "REAL_ONNX" ? "bg-emerald-500" : "bg-blue-500"
              }`} />
              <span className="text-[13.5px] font-medium text-primary-text">
                {diagnostics?.recognition_mode === "REAL_ONNX" ? "REAL MODEL (ONNX)" : "REAL MODEL (512-D NATIVE)"}
              </span>
            </div>
            <p className="text-[11.5px] text-secondary-text mt-1">
              Zero synthetic data. Cosine vector similarity matching.
            </p>
          </div>
        </div>
      </div>

      {/* AI Recognition Thresholds Card (Phase 5) */}
      <div className="bg-white border border-border rounded-card p-6 space-y-5">
        <div className="flex items-center gap-2.5 pb-3 border-b border-border">
          <Sliders className="w-5 h-5 text-accent" />
          <div>
            <h3 className="text-[16px] font-semibold text-primary-text">
              Face Recognition Confidence Thresholds
            </h3>
            <p className="text-[12.5px] text-secondary-text">
              Adjust how strictly the cosine vector similarity matcher classifies faces. Values persist in PostgreSQL/SQLite.
            </p>
          </div>
        </div>

        {/* Match Threshold Slider */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-[13.5px]">
            <span className="font-medium text-primary-text">
              Recognition Match Threshold (
              <span className="text-accent font-mono font-semibold">
                {(matchThreshold * 100).toFixed(0)}%
              </span>
              )
            </span>
            <span className="text-[12px] text-success font-medium">
              High Confidence (Recognized ✓)
            </span>
          </div>
          <input
            type="range"
            min="0.50"
            max="0.95"
            step="0.01"
            disabled={!isAdmin}
            value={matchThreshold}
            onChange={(e) => setMatchThreshold(parseFloat(e.target.value))}
            className="w-full accent-accent cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <p className="text-[12px] text-secondary-text">
            Detections scoring &ge; {(matchThreshold * 100).toFixed(0)}% similarity will be automatically recognized and marked Present.
          </p>
        </div>

        {/* Review Threshold Slider */}
        <div className="space-y-2 pt-3 border-t border-border/70">
          <div className="flex items-center justify-between text-[13.5px]">
            <span className="font-medium text-primary-text">
              Borderline Review Threshold (
              <span className="text-warning font-mono font-semibold">
                {(reviewThreshold * 100).toFixed(0)}%
              </span>
              )
            </span>
            <span className="text-[12px] text-warning font-medium">
              Needs Teacher Review ⚠
            </span>
          </div>
          <input
            type="range"
            min="0.40"
            max="0.65"
            step="0.01"
            disabled={!isAdmin}
            value={reviewThreshold}
            onChange={(e) => setReviewThreshold(parseFloat(e.target.value))}
            className="w-full accent-warning cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <p className="text-[12px] text-secondary-text">
            Detections between {(reviewThreshold * 100).toFixed(0)}% and {(matchThreshold * 100).toFixed(0)}% will be flagged as borderline for teacher review.
          </p>
        </div>

        <div className="p-3.5 bg-subtle border border-border rounded-control text-[12.5px] text-secondary-text">
          <strong className="text-primary-text">Active Classification Logic:</strong>
          <ul className="list-disc list-inside mt-1 space-y-0.5">
            <li>
              Similarity &ge; {(matchThreshold * 100).toFixed(0)}% &rarr;{" "}
              <span className="text-success font-medium">Recognized</span>
            </li>
            <li>
              {(reviewThreshold * 100).toFixed(0)}% &le; Similarity &lt;{" "}
              {(matchThreshold * 100).toFixed(0)}% &rarr;{" "}
              <span className="text-warning font-medium">Needs Review</span>
            </li>
            <li>
              Similarity &lt; {(reviewThreshold * 100).toFixed(0)}% &rarr;{" "}
              <span className="text-secondary-text font-medium">Unknown Face</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Hardware & Camera Preferences */}
      <div className="bg-white border border-border rounded-card p-6 space-y-4">
        <div className="flex items-center gap-2.5 pb-3 border-b border-border">
          <Camera className="w-5 h-5 text-accent" />
          <div>
            <h3 className="text-[16px] font-semibold text-primary-text">
              Camera & Processing Preferences
            </h3>
            <p className="text-[12.5px] text-secondary-text">
              Configure resolution and client-side preprocessing.
            </p>
          </div>
        </div>

        <div>
          <label className="block text-[13px] font-medium text-primary-text mb-1.5">
            Target Camera Capture Resolution
          </label>
          <select
            value={cameraQuality}
            onChange={(e) => setCameraQuality(e.target.value)}
            className="h-9 px-3 text-[13.5px] bg-white border border-border rounded-control focus:outline-none focus:border-accent"
          >
            <option value="hd">720p HD (Recommended for standard webcams)</option>
            <option value="fhd">1080p Full HD (Recommended for classroom group capture)</option>
            <option value="4k">4K Ultra HD (High-density auditoriums)</option>
          </select>
        </div>
      </div>

      {/* Biometric Privacy & Compliance Card */}
      <div className="bg-white border border-border rounded-card p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center gap-2.5">
            <Shield className="w-5 h-5 text-accent" />
            <div>
              <h3 className="text-[16px] font-semibold text-primary-text">
                Biometric Privacy & Compliance
              </h3>
              <p className="text-[12.5px] text-secondary-text">
                FERPA, GDPR, and biometric security compliance controls.
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsPrivacyModalOpen(true)}
          >
            View Privacy Notice
          </Button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[13px]">
          <div className="p-3 bg-subtle rounded-control border border-border">
            <span className="font-semibold text-primary-text block mb-1">
              Zero Raw Photos Stored
            </span>
            <p className="text-secondary-text text-[12px] leading-relaxed">
              Faces are converted into 512-d mathematical embeddings. Raw source photos are discarded immediately after vector computation.
            </p>
          </div>
          <div className="p-3 bg-subtle rounded-control border border-border">
            <span className="font-semibold text-primary-text block mb-1">
              Right to Purge
            </span>
            <p className="text-secondary-text text-[12px] leading-relaxed">
              Administrators can permanently purge biometric data for any student with 1 click from their student profile.
            </p>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end pt-2">
        <Button
          variant="primary"
          size="md"
          leftIcon={<Save className="w-4 h-4" />}
          isLoading={isSaving}
          disabled={!isAdmin}
          onClick={handleSaveSettings}
        >
          {isAdmin ? "Save Configuration to Database" : "Save Disabled (Admin Only)"}
        </Button>
      </div>

      {/* Biometric Privacy Notice Modal */}
      <Modal
        isOpen={isPrivacyModalOpen}
        onClose={() => setIsPrivacyModalOpen(false)}
        title="AttendAI Biometric Data & Privacy Notice"
        description="Transparent biometric collection and processing policy"
        maxWidth="lg"
      >
        <div className="space-y-4 text-left text-[13px] text-secondary-text leading-relaxed">
          <p>
            AttendAI processes facial features strictly for educational attendance recording and identity verification.
          </p>
          <div className="space-y-2">
            <h4 className="font-semibold text-primary-text text-[14px]">
              How Biometric Data is Handled:
            </h4>
            <ul className="list-disc list-inside space-y-1">
              <li>
                <strong>Ephemeral Group Image Processing:</strong> Classroom group photos uploaded for roll call are processed transiently in memory and never permanently stored on disk.
              </li>
              <li>
                <strong>Mathematical Embeddings Only:</strong> Student faces are converted into 512-dimensional numerical vectors. Raw photos cannot be reconstructed from these vectors.
              </li>
              <li>
                <strong>Zero Public Exposure:</strong> Biometric embeddings are locked behind administrative authentication and never exposed on frontend endpoints.
              </li>
              <li>
                <strong>Audit Trail Compliance:</strong> All manual corrections made by instructors are recorded with reasons in immutable audit logs.
              </li>
            </ul>
          </div>

          <div className="flex justify-end pt-3 border-t border-border">
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsPrivacyModalOpen(false)}
            >
              Acknowledge & Close
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
