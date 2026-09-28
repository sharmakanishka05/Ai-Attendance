"use client";

import React, { useRef, useState, useEffect, useCallback } from "react";
import {
  Camera,
  RefreshCw,
  X,
  AlertCircle,
  Play,
  Square,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Sparkles,
  Layers,
  Activity,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { api } from "@/lib/api";
import { LiveFaceResult } from "@/types";

interface CameraCaptureProps {
  onCapture: (imageBase64: string) => void;
  onCancel: () => void;
  sessionId?: string;
  classId?: string;
}

export const CameraCapture: React.FC<CameraCaptureProps> = ({
  onCapture,
  onCancel,
  sessionId,
  classId,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>("");
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  // Real-Time Dev Test Mode State
  const [isLiveRecognitionActive, setIsLiveRecognitionActive] = useState(false);
  const [liveFaces, setLiveFaces] = useState<LiveFaceResult[]>([]);
  const [lastLatencyMs, setLastLatencyMs] = useState<number | null>(null);
  const [isProcessingFrame, setIsProcessingFrame] = useState(false);
  const liveIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize camera
  const startCamera = async (deviceId?: string) => {
    setIsInitializing(true);
    setError(null);

    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }

    try {
      const constraints: MediaStreamConstraints = {
        video: deviceId
          ? { deviceId: { exact: deviceId } }
          : { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      };

      const newStream = await navigator.mediaDevices.getUserMedia(constraints);
      setStream(newStream);
      if (videoRef.current) {
        videoRef.current.srcObject = newStream;
      }

      // Enumerate devices for camera switching
      const allDevices = await navigator.mediaDevices.enumerateDevices();
      const videoInputs = allDevices.filter((d) => d.kind === "videoinput");
      setDevices(videoInputs);
      if (!selectedDeviceId && videoInputs.length > 0) {
        setSelectedDeviceId(videoInputs[0].deviceId);
      }
    } catch (err: any) {
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        setError("Camera permission was denied. Please allow camera access in your browser settings to take live attendance.");
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        setError("No camera device was detected on your system.");
      } else {
        setError(`Unable to access camera: ${err.message || "Unknown error"}`);
      }
    } finally {
      setIsInitializing(false);
    }
  };

  useEffect(() => {
    startCamera();
    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
      if (liveIntervalRef.current) {
        clearInterval(liveIntervalRef.current);
      }
    };
  }, []);

  const switchCamera = () => {
    if (devices.length <= 1) return;
    const currentIndex = devices.findIndex((d) => d.deviceId === selectedDeviceId);
    const nextIndex = (currentIndex + 1) % devices.length;
    const nextDevice = devices[nextIndex];
    setSelectedDeviceId(nextDevice.deviceId);
    startCamera(nextDevice.deviceId);
  };

  // Perform a live recognition tick on current camera frame
  const processCurrentFrame = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current || isProcessingFrame) return;
    const video = videoRef.current;
    if (video.readyState < 2 || video.videoWidth === 0) return;

    const canvas = canvasRef.current;
    canvas.width = Math.min(video.videoWidth, 800);
    canvas.height = Math.min(video.videoHeight, 600);

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const base64 = canvas.toDataURL("image/jpeg", 0.85);

    setIsProcessingFrame(true);
    const startTime = performance.now();

    try {
      const formData = new FormData();
      formData.append("image_base64", base64);
      if (sessionId) formData.append("session_id", sessionId);
      if (classId) formData.append("class_id", classId);

      const res = await api.recognizeAndMark(formData);
      const elapsed = Math.round(performance.now() - startTime);
      setLastLatencyMs(elapsed);

      if (res.faces && res.faces.length > 0) {
        setLiveFaces(res.faces);
      } else if (res.face_detected && res.student_name) {
        setLiveFaces([
          {
            box_id: "face_live_1",
            bbox: { x: 25, y: 20, width: 50, height: 60 },
            student_id: res.student_id,
            student_name: res.student_name,
            confidence: res.confidence,
            status: res.recognized ? "recognized" : "unknown",
            attendance_marked: res.attendance_marked,
            attendance_status: res.attendance_marked ? "PRESENT" : res.reason || "RECORDED",
            reason: res.reason,
          },
        ]);
      } else {
        setLiveFaces([]);
      }
    } catch (e: any) {
      console.warn("Live frame recognition tick failed:", e);
    } finally {
      setIsProcessingFrame(false);
    }
  }, [isProcessingFrame, sessionId, classId]);

  // Toggle Continuous Real-Time Dev Test Mode
  useEffect(() => {
    if (isLiveRecognitionActive) {
      // Process frame every 900ms to balance accuracy and CPU load
      liveIntervalRef.current = setInterval(processCurrentFrame, 900);
    } else {
      if (liveIntervalRef.current) {
        clearInterval(liveIntervalRef.current);
        liveIntervalRef.current = null;
      }
      setLiveFaces([]);
      setLastLatencyMs(null);
    }
    return () => {
      if (liveIntervalRef.current) {
        clearInterval(liveIntervalRef.current);
      }
    };
  }, [isLiveRecognitionActive, processCurrentFrame]);

  // Load a test sample image into captured state for immediate camera simulation
  const handleLoadSampleFrame = async (samplePath: string) => {
    try {
      const res = await fetch(samplePath);
      const blob = await res.blob();
      const reader = new FileReader();
      reader.onloadend = () => {
        const b64 = reader.result as string;
        setCapturedImage(b64);
        // Also run recognition on sample
        runSingleFrameRecognition(b64);
      };
      reader.readAsDataURL(blob);
    } catch (err: any) {
      console.error("Failed to load sample:", err);
    }
  };

  const runSingleFrameRecognition = async (b64: string) => {
    try {
      const formData = new FormData();
      formData.append("image_base64", b64);
      if (sessionId) formData.append("session_id", sessionId);
      if (classId) formData.append("class_id", classId);

      const startTime = performance.now();
      const res = await api.recognizeAndMark(formData);
      setLastLatencyMs(Math.round(performance.now() - startTime));

      if (res.faces && res.faces.length > 0) {
        setLiveFaces(res.faces);
      } else {
        setLiveFaces([]);
      }
    } catch (e) {
      console.warn("Sample recognition failed:", e);
    }
  };

  const handleCapture = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const base64 = canvas.toDataURL("image/jpeg", 0.9);
    setCapturedImage(base64);
    runSingleFrameRecognition(base64);
  };

  const handleRetake = () => {
    setCapturedImage(null);
    setLiveFaces([]);
  };

  const handleConfirm = () => {
    if (capturedImage) {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
      onCapture(capturedImage);
    }
  };

  return (
    <div className="bg-white border border-border rounded-card p-5 text-left space-y-4">
      {/* Top Header & Mode Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-border">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-[15px] font-semibold text-primary-text">
              Live Camera Attendance & Recognition
            </h3>
            <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-accent-subtle text-accent border border-accent/20">
              SFace 128-D
            </span>
          </div>
          <p className="text-[13px] text-secondary-text mt-0.5">
            Real-time YuNet detection + OpenCV SFace cosine similarity (Threshold: 0.70).
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Continuous Recognition Dev Mode Toggle */}
          <button
            onClick={() => setIsLiveRecognitionActive(!isLiveRecognitionActive)}
            className={`px-3 py-1.5 rounded-control text-[12px] font-medium transition-all flex items-center gap-1.5 border ${
              isLiveRecognitionActive
                ? "bg-success text-white border-success shadow-xs"
                : "bg-subtle text-secondary-text border-border hover:text-primary-text"
            }`}
          >
            {isLiveRecognitionActive ? (
              <>
                <Square className="w-3.5 h-3.5 fill-current" />
                <span>Live Test Mode: ACTIVE</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Start Live Recognition Mode</span>
              </>
            )}
          </button>

          <button
            onClick={onCancel}
            className="p-1.5 rounded-control text-secondary-text hover:text-primary-text hover:bg-subtle"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Quick Test Frame Selector (for headless testing or validating camera frames) */}
      <div className="p-3 bg-subtle border border-border rounded-control flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5 text-[12px]">
        <div className="flex items-center gap-1.5 text-secondary-text">
          <Sparkles className="w-3.5 h-3.5 text-accent" />
          <span className="font-semibold text-primary-text">Simulate Camera Input:</span>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            type="button"
            onClick={() => handleLoadSampleFrame("/test_data/webcam_MCA001_new.jpg")}
            className="px-2 py-1 bg-white hover:bg-subtle border border-border rounded text-[11px] font-medium text-primary-text"
          >
            Kanishka (New Webcam)
          </button>
          <button
            type="button"
            onClick={() => handleLoadSampleFrame("/test_data/webcam_MCA002_new.jpg")}
            className="px-2 py-1 bg-white hover:bg-subtle border border-border rounded text-[11px] font-medium text-primary-text"
          >
            Namita (New Webcam)
          </button>
          <button
            type="button"
            onClick={() => handleLoadSampleFrame("/test_data/webcam_MCA003_new.jpg")}
            className="px-2 py-1 bg-white hover:bg-subtle border border-border rounded text-[11px] font-medium text-primary-text"
          >
            Akanksha (New Webcam)
          </button>
          <button
            type="button"
            onClick={() => handleLoadSampleFrame("/test_data/webcam_multi_two_students.jpg")}
            className="px-2 py-1 bg-white hover:bg-subtle border border-border rounded text-[11px] font-medium text-primary-text"
          >
            Two Students
          </button>
          <button
            type="button"
            onClick={() => handleLoadSampleFrame("/test_data/webcam_multi_registered_and_unknown.jpg")}
            className="px-2 py-1 bg-white hover:bg-subtle border border-border rounded text-[11px] font-medium text-primary-text"
          >
            1 Student + Unknown
          </button>
          <button
            type="button"
            onClick={() => handleLoadSampleFrame("/test_data/unknown_person.jpg")}
            className="px-2 py-1 bg-white hover:bg-danger-subtle border border-danger-border rounded text-[11px] font-medium text-danger"
          >
            Unknown Person
          </button>
          <button
            type="button"
            onClick={() => handleLoadSampleFrame("/test_data/webcam_no_face.jpg")}
            className="px-2 py-1 bg-white hover:bg-subtle border border-border rounded text-[11px] font-medium text-secondary-text"
          >
            No Face
          </button>
        </div>
      </div>

      {error ? (
        <div className="p-4 bg-danger-subtle border border-danger-border rounded-card text-danger flex items-start gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block text-[14px]">Camera Feed Notice</span>
            <p className="text-[13px] mt-0.5 leading-relaxed">{error}</p>
            <p className="text-[12px] text-secondary-text mt-1">
              You can still test real camera recognition using the &quot;Simulate Camera Input&quot; buttons above.
            </p>
            <Button
              variant="outline"
              size="sm"
              className="mt-3 bg-white"
              onClick={() => startCamera(selectedDeviceId)}
            >
              Try Initializing Again
            </Button>
          </div>
        </div>
      ) : (
        <div className="relative bg-black rounded-card overflow-hidden aspect-video flex items-center justify-center border border-border select-none">
          {capturedImage ? (
            <img
              src={capturedImage}
              alt="Captured frame"
              className="w-full h-full object-contain"
            />
          ) : (
            <>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
              />

              {/* Viewfinder overlay when idle */}
              {!isLiveRecognitionActive && liveFaces.length === 0 && (
                <div className="absolute inset-10 border border-white/25 rounded-card pointer-events-none flex items-center justify-center">
                  <span className="text-[11px] text-white/70 font-medium tracking-wide uppercase px-3 py-1 rounded bg-black/40 backdrop-blur-sm">
                    Center face within frame
                  </span>
                </div>
              )}
            </>
          )}

          {/* Dynamic Bounding Boxes Layer */}
          {liveFaces.map((face) => {
            const isRecognized = face.status === "recognized";
            const isReview = face.status === "review";
            const isUnknown = face.status === "unknown";

            let borderColor = "border-danger";
            let tagBg = "bg-danger text-white";
            if (isRecognized) {
              borderColor = "border-[#16803C]";
              tagBg = "bg-[#16803C] text-white";
            } else if (isReview) {
              borderColor = "border-[#B7791F]";
              tagBg = "bg-[#B7791F] text-white";
            }

            return (
              <div
                key={face.box_id}
                style={{
                  left: `${face.bbox.x}%`,
                  top: `${face.bbox.y}%`,
                  width: `${face.bbox.width}%`,
                  height: `${face.bbox.height}%`,
                }}
                className={`absolute border-2 transition-all duration-150 pointer-events-none ${borderColor}`}
              >
                {/* Floating recognition label */}
                <div
                  className={`absolute -top-7 left-0 px-2 py-0.5 rounded text-[11px] font-semibold whitespace-nowrap shadow-sm flex items-center gap-1.5 ${tagBg}`}
                >
                  {isRecognized && <CheckCircle2 className="w-3 h-3" />}
                  {isReview && <AlertTriangle className="w-3 h-3" />}
                  {isUnknown && <HelpCircle className="w-3 h-3" />}

                  <span>
                    {isRecognized
                      ? `${face.student_name} (${face.student_id})`
                      : isReview
                      ? `${face.student_name || "Ambiguous"} (Review)`
                      : "UNKNOWN PERSON"}
                  </span>

                  <span className="opacity-90 tabular-nums font-mono text-[10px]">
                    {(face.confidence * 100).toFixed(0)}%
                  </span>

                  {face.attendance_marked && (
                    <span className="ml-1 px-1 bg-white/20 rounded text-[9.5px] uppercase font-bold tracking-wider">
                      PRESENT
                    </span>
                  )}
                  {face.reason === "ALREADY_MARKED" && (
                    <span className="ml-1 px-1 bg-white/20 rounded text-[9.5px] uppercase font-bold tracking-wider">
                      MARKED
                    </span>
                  )}
                </div>
              </div>
            );
          })}

          {isInitializing && (
            <div className="absolute inset-0 bg-black/60 flex items-center justify-center text-white text-[13px]">
              Initializing camera feed...
            </div>
          )}

          {/* Top Live Status Indicator Bar */}
          <div className="absolute top-3 left-3 flex items-center gap-2">
            <span className="px-2 py-1 rounded bg-black/70 backdrop-blur-sm text-white text-[11px] font-mono flex items-center gap-1.5 border border-white/10">
              <span
                className={`w-2 h-2 rounded-full ${
                  isLiveRecognitionActive ? "bg-success animate-ping" : "bg-white/40"
                }`}
              />
              {isLiveRecognitionActive ? "LIVE AI SCANNING" : "CAMERA READY"}
            </span>

            {lastLatencyMs !== null && (
              <span className="px-2 py-1 rounded bg-black/70 backdrop-blur-sm text-white/90 text-[11px] font-mono border border-white/10">
                {lastLatencyMs}ms
              </span>
            )}
          </div>
        </div>
      )}

      {/* Hidden canvas for capturing and scaling frames */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Live Detections Breakdown (Task 2, 3, 4: Display Name, ID, Confidence, Status, Attendance) */}
      {liveFaces.length > 0 && (
        <div className="p-3.5 bg-subtle border border-border rounded-control space-y-2">
          <div className="flex items-center justify-between text-[12px] font-semibold text-secondary-text">
            <span>Detected Faces in Camera ({liveFaces.length})</span>
            <span>Threshold: 0.70</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
            {liveFaces.map((f, i) => {
              const isRec = f.status === "recognized";
              const isRev = f.status === "review";
              const isUnk = f.status === "unknown";

              return (
                <div
                  key={f.box_id || i}
                  className={`p-3 bg-white border rounded-control space-y-1.5 shadow-2xs ${
                    isRec
                      ? "border-success/40"
                      : isRev
                      ? "border-warning/40"
                      : "border-danger/40"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono text-secondary-text">
                      Face #{i + 1}
                    </span>
                    <Badge
                      variant={isRec ? "recognized" : isRev ? "review" : "unknown"}
                      size="sm"
                    >
                      {isRec ? "RECOGNIZED" : isRev ? "REVIEW" : "UNKNOWN"}
                    </Badge>
                  </div>

                  <div>
                    <div className="text-[13px] font-semibold text-primary-text truncate">
                      {isRec ? f.student_name : isRev ? f.student_name || "Uncertain" : "UNKNOWN PERSON"}
                    </div>
                    <div className="text-[11px] text-secondary-text font-mono">
                      Student ID: {f.student_id || "N/A"}
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-1 border-t border-border/60 text-[11px]">
                    <span className="text-secondary-text">
                      Confidence: <b className="font-mono">{(f.confidence * 100).toFixed(0)}%</b>
                    </span>
                    <span
                      className={`font-semibold ${
                        f.attendance_marked
                          ? "text-success"
                          : f.reason === "ALREADY_MARKED"
                          ? "text-accent"
                          : "text-secondary-text"
                      }`}
                    >
                      {f.attendance_marked
                        ? "PRESENT"
                        : f.reason === "ALREADY_MARKED"
                        ? "ALREADY_MARKED"
                        : "NO ATTENDANCE"}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {capturedImage && liveFaces.length === 0 && !isProcessingFrame && (
        <div className="p-3 bg-subtle border border-border rounded-control text-[12px] text-secondary-text flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-secondary-text flex-shrink-0" />
          <span>No face detected in this camera frame (NO_FACE_DETECTED). Attendance not marked.</span>
        </div>
      )}

      {/* Bottom Camera Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <div className="text-[12px] text-secondary-text flex items-center gap-2">
          {devices.length > 1 && !capturedImage && (
            <Button
              variant="outline"
              size="sm"
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
              onClick={switchCamera}
            >
              Switch Camera
            </Button>
          )}
        </div>

        <div className="flex items-center gap-2">
          {capturedImage ? (
            <>
              <Button variant="secondary" size="sm" onClick={handleRetake}>
                Retake
              </Button>
              <Button variant="primary" size="sm" onClick={handleConfirm}>
                Submit For Review
              </Button>
            </>
          ) : (
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Camera className="w-4 h-4" />}
              onClick={handleCapture}
              disabled={isInitializing || !!error}
            >
              Capture Attendance Frame
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
