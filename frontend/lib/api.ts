import {
  Student,
  StudentDetail,
  ClassModel,
  AttendanceSession,
  ProcessImageResult,
  AttendanceReportSummary,
  AuditLogItem,
  QualityFeedback,
  User,
  RecognizeAndMarkResult
} from "@/types";

function getApiBase(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (envUrl) {
    if (envUrl === "/api" || envUrl === "/api/") {
      return "/api";
    }
    const clean = envUrl.replace(/\/+$/, "");
    return clean.endsWith("/api") ? clean : `${clean}/api`;
  }
  // In production (Vercel), default to relative "/api" proxy to Render
  // Never fall back to localhost in production
  if (process.env.NODE_ENV === "production" || typeof window !== "undefined") {
    return "/api";
  }
  return "http://127.0.0.1:8000/api";
}

const API_BASE = getApiBase();

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem("attendai_token");
  if (token) return token;
  const match = document.cookie.match(/(?:^|;\s*)auth_token=([^;]+)/);
  return match ? match[1] : null;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const token = getAuthToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };
  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(url, {
      ...options,
      credentials: "include", // Send HTTP-only auth cookies
      headers,
    });

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      const message = errBody.detail || `HTTP error ${res.status}`;
      throw new Error(message);
    }

    return await res.json();
  } catch (error: any) {
    console.warn(`[API] Fetch failed for ${url}:`, error.message);
    throw error;
  }
}

export const api = {
  // --- Auth ---
  login: async (email: string, password: string): Promise<{ access_token: string; user: User }> => {
    const data = await request<{ access_token: string; user: User }>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (typeof window !== "undefined" && data.access_token) {
      localStorage.setItem("attendai_token", data.access_token);
      localStorage.setItem("attendai_user", JSON.stringify(data.user));
    }
    return data;
  },

  logout: async (): Promise<{ success: boolean; message: string }> => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("attendai_token");
      localStorage.removeItem("attendai_user");
    }
    return request<{ success: boolean; message: string }>("/auth/logout", {
      method: "POST",
    });
  },

  getMe: async (): Promise<User> => {
    return request<User>("/auth/me");
  },

  // --- Settings & Diagnostics ---
  getSettings: async (): Promise<{
    face_match_threshold: number;
    face_review_threshold: number;
    app_env: string;
    diagnostics: {
      face_detector: string;
      embedding_model: string;
      recognition_mode: string;
      onnx_model_file_present: boolean;
    };
  }> => {
    return request("/settings");
  },

  updateSettings: async (payload: {
    face_match_threshold?: number;
    face_review_threshold?: number;
  }): Promise<{ success: boolean; message: string }> => {
    return request("/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },

  // --- Dashboard & Reports ---
  getDashboardReport: async (classId?: string, days: number = 14): Promise<AttendanceReportSummary> => {
    const params = new URLSearchParams();
    if (classId) params.append("class_id", classId);
    params.append("days", days.toString());
    return request<AttendanceReportSummary>(`/reports/attendance?${params.toString()}`);
  },

  getAuditLogs: async (limit: number = 50): Promise<AuditLogItem[]> => {
    return request<AuditLogItem[]>(`/reports/audit?limit=${limit}`);
  },

  downloadCSV: async (classId?: string): Promise<Blob> => {
    const params = new URLSearchParams();
    if (classId && classId !== "all") params.append("class_id", classId);
    const url = `${API_BASE}/reports/export-csv?${params.toString()}`;
    const token = getAuthToken();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(url, { credentials: "include", headers });
    if (!res.ok) throw new Error("Failed to download CSV");
    return await res.blob();
  },

  downloadExcel: async (classId?: string): Promise<Blob> => {
    const params = new URLSearchParams();
    if (classId && classId !== "all") params.append("class_id", classId);
    const url = `${API_BASE}/reports/export-excel?${params.toString()}`;
    const token = getAuthToken();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(url, { credentials: "include", headers });
    if (!res.ok) throw new Error("Failed to download Excel report");
    return await res.blob();
  },

  // --- Students ---
  getStudents: async (params?: { search?: string; class_name?: string; section?: string; has_face?: boolean }): Promise<Student[]> => {
    const query = new URLSearchParams();
    if (params?.search) query.append("search", params.search);
    if (params?.class_name) query.append("class_name", params.class_name);
    if (params?.section) query.append("section", params.section);
    if (params?.has_face !== undefined) query.append("has_face", String(params.has_face));
    return request<Student[]>(`/students?${query.toString()}`);
  },

  getStudentDetail: async (id: string): Promise<StudentDetail> => {
    return request<StudentDetail>(`/students/${id}`);
  },

  createStudent: async (data: { name: string; roll_number: string; class_name: string; section: string; email?: string }): Promise<Student> => {
    return request<Student>("/students", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  },

  registerStudentFace: async (id: string, file?: File, imageBase64?: string): Promise<{ success: boolean; message: string; quality: QualityFeedback }> => {
    const formData = new FormData();
    if (file) {
      formData.append("file", file);
    } else if (imageBase64) {
      formData.append("image_base64", imageBase64);
    }
    return request<{ success: boolean; message: string; quality: QualityFeedback }>(`/students/${id}/face-registration`, {
      method: "POST",
      body: formData,
    });
  },

  deleteStudentFaceData: async (id: string): Promise<{ success: boolean; message: string }> => {
    return request<{ success: boolean; message: string }>(`/students/${id}/face-data`, {
      method: "DELETE",
    });
  },

  deleteStudent: async (id: string): Promise<{ success: boolean; message: string }> => {
    return request<{ success: boolean; message: string }>(`/students/${id}`, {
      method: "DELETE",
    });
  },

  // --- Classes ---
  getClasses: async (): Promise<ClassModel[]> => {
    return request<ClassModel[]>("/classes");
  },

  createClass: async (data: { name: string; course: string; section: string; teacher_name?: string; schedule?: string }): Promise<ClassModel> => {
    return request<ClassModel>("/classes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  },

  getClassDetail: async (id: string): Promise<any> => {
    return request<any>(`/classes/${id}`);
  },

  // --- Sessions ---
  getSessions: async (classId?: string, statusFilter?: string): Promise<AttendanceSession[]> => {
    const query = new URLSearchParams();
    if (classId) query.append("class_id", classId);
    if (statusFilter) query.append("status_filter", statusFilter);
    return request<AttendanceSession[]>(`/sessions?${query.toString()}`);
  },

  createSession: async (data: { class_id: string; date: string; time: string; title: string }): Promise<AttendanceSession> => {
    return request<AttendanceSession>("/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  },

  getSessionDetail: async (id: string): Promise<any> => {
    return request<any>(`/sessions/${id}`);
  },

  // --- Attendance CV Processing ---
  processAttendanceImage: async (formData: FormData): Promise<ProcessImageResult> => {
    return request<ProcessImageResult>("/attendance/process-image", {
      method: "POST",
      body: formData,
    });
  },

  confirmAttendance: async (payload: {
    session_id: string;
    items: Array<{ student_id: string; status: string; confidence: number; marked_method: string }>;
    unknown_faces_handled?: number;
    notes?: string;
  }): Promise<{ success: boolean; message: string; data: any }> => {
    return request<{ success: boolean; message: string; data: any }>("/attendance/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },

  recognizeAndMark: async (formData: FormData): Promise<RecognizeAndMarkResult> => {
    return request<RecognizeAndMarkResult>("/attendance/recognize-and-mark", {
      method: "POST",
      body: formData,
    });
  },

  correctAttendance: async (payload: {
    record_id: string;
    new_status: string;
    reason: string;
  }): Promise<{ success: boolean; message: string }> => {
    return request<{ success: boolean; message: string }>("/attendance/correct", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },
};
