# AttendAI

> *"Smart attendance, without the paperwork."*

AttendAI is a production-quality, privacy-conscious attendance management SaaS built for educational institutions and organizations. It replaces manual roll calls and sign-in sheets with real-time multi-face computer vision recognition, seamless group classroom photo processing, human-in-the-loop review, and audit-logged attendance records.

---

## Key Features

- **Multi-Face Group Photo Recognition**: Detects, aligns, and matches 1 to 40+ faces in a single classroom photograph using OpenCV YuNet DNN and SFace ONNX neural networks.
- **Strict Zero Fake AI**: Never fabricates students, dummy confidence numbers, or synthetic bounding boxes. If the backend fails to analyze an image, an actionable error banner with retry options is displayed.
- **Enterprise Authentication & RBAC**: Real HTTP-only cookie-based sessions with server-side Role-Based Access Control distinguishing `admin` (student/class management, biometric purge, system configuration) from `teacher` (view assigned classes, conduct roll call, manual review).
- **Persistent System Settings**: Database-backed `system_settings` table for runtime configuration of `FACE_MATCH_THRESHOLD` and `FACE_REVIEW_THRESHOLD`.
- **Database Versioning via Alembic**: Automated, version-controlled database schema migrations supporting both PostgreSQL and SQLite.
- **Single-Image Deduplication**: Automatically detects multiple detections of the same student in a single photo and retains the highest-confidence match.
- **Human-in-the-Loop Review**: Allows teachers to verify AI classifications, adjust attendance status (Present, Late, Absent), and assign unknown faces before committing.
- **Mandatory Audit Logging**: Tracks every manual correction with the instructor's ID, previous status, updated status, reason, and immutable timestamp.
- **Duplicate Attendance Prevention**: Enforces database-level unique constraints on `(session_id, student_id)` and concurrency safety locks.
- **Privacy & Biometric Compliance**: FERPA/GDPR aligned. Ephemeral image processing, encrypted embeddings, zero public vector endpoints, and a 1-click **"Delete Face Data"** capability.
- **Reporting & Dual Format Export**: One-click **CSV Export** and styled **Excel Spreadsheet (.xlsx)** export via `openpyxl`.

---

## Technology Stack

- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS with custom design tokens, Lucide React, Playwright E2E.
- **Backend**: Python 3.11, FastAPI, SQLAlchemy ORM, Alembic migrations, Pydantic v2, openpyxl.
- **Computer Vision**: OpenCV YuNet DNN detector (`face_detection_yunet.onnx`) + SFace / ArcFace ONNX face embedding neural network + Cosine similarity search.
- **Database**: PostgreSQL 16 with pgvector (primary production) / SQLite (development).
- **Containerization**: Docker & Docker Compose.

---

## Design System & Aesthetic

AttendAI rejects generic AI templates, exaggerated gradients, and bloated cards. The UI is built around a calm, distraction-free SaaS design system:
- **Canvas Background**: `#F7F7F5` (Warm off-white neutral)
- **Surfaces**: `#FFFFFF` (Crisp cards with subtle `#E7E7E3` borders)
- **Primary Text**: `#171717` (Dark charcoal)
- **Accent**: `#3157D5` (Restrained cobalt/indigo)
- **Status Indicators**: `#16803C` (Success/Present), `#B7791F` (Warning/Late/Review), `#C53030` (Danger/Absent).
- **Accessibility**: ARIA dialog roles, focus trapping, focus restoration, and keyboard navigation.

---

## Quickstart (Local Development)

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- (Optional) Docker & Docker Compose

### 1. Database Migrations & Backend Startup

```bash
cd backend
python -m venv venv

# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Run Alembic migrations to initialize schema
alembic upgrade head

# Run FastAPI server
uvicorn app.main:app --port 8000
```
Backend will be live at `http://127.0.0.1:8000` (Swagger docs available at `http://127.0.0.1:8000/docs`).

### 2. Frontend Startup

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## Seed Accounts & Role Credentials

The database comes pre-seeded with the administrator account for faculty access:

| Role | Name | Email | Password | Permissions |
|---|---|---|---|---|
| **Administrator & Instructor** | Ajeet Singh | `ajeet.singh@kit.ac.in` | `password123` | Full access: Student CRUD, Biometric purge, Class creation, System settings, Audit logs, Attendance roll call |

---

## Computer Vision Neural Models

AttendAI requires real neural network models located in `backend/models/`:

1. **Face Detector**: `face_detection_yunet.onnx` (~232 KB) — YuNet deep neural face detector.
2. **Face Recognizer**: `face_recognition_sface.onnx` (~38.6 MB) — SFace deep neural feature extractor producing unit-normalized facial embeddings.

Diagnostics are displayed dynamically under **Settings -> Computer Vision Model Diagnostics**:
- Face Detector: `READY (YuNet DNN)`
- Embedding Model: `READY (SFace ONNX DNN)`
- Recognition Mode: `REAL MODEL`

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `APP_ENV` | Application environment (`development` or `production`) | `production` |
| `DATABASE_URL` | PostgreSQL connection string or SQLite fallback | `sqlite:///./attendai.db` |
| `JWT_SECRET` | Secret key for JWT session tokens | `attendai_super_secret...` |
| `FACE_MATCH_THRESHOLD` | Minimum cosine similarity for automatic match | `0.70` |
| `FACE_REVIEW_THRESHOLD` | Threshold below which face is considered unknown | `0.52` |
| `MAX_UPLOAD_SIZE_MB` | Maximum allowed photo upload size | `15` |
| `NEXT_PUBLIC_API_URL` | Backend URL for frontend client | `http://127.0.0.1:8000/api` |
| `NEXT_PUBLIC_ENABLE_MOCK_AI` | Explicit mock toggle (strictly disabled in production) | `false` |

---

## Running Automated Tests

### Backend Unit, Security, & End-to-End Suite (Pytest)

```bash
cd backend
.\venv\Scripts\python -m pytest -o pythonpath=. -v
```
Runs 24 automated tests including:
- `test_security.py`: RBAC enforcement, 401 unauthenticated rejection, 403 teacher restrictions, expired tokens, biometric privacy, zero vector leaks.
- `test_concurrency.py`: Concurrent attendance confirmation race-condition safety.
- `test_e2e_real_pipeline.py`: Full end-to-end real attendance pipeline.
- `test_face_pipeline.py`: Real CV quality checks, cosine similarity, threshold classification.
- `test_reports.py`: Attendance reports, CSV download, Excel XLSX download.

### Frontend Browser E2E Suite (Playwright)

```bash
cd frontend
npx playwright test
```

---

## Docker Compose Setup

To launch the full production stack (PostgreSQL with pgvector, FastAPI backend with automatic migrations, and Next.js frontend):

```bash
docker-compose up --build
```
