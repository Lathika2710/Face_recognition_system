# FaceAI — AI Face Recognition & Smart Attendance System

A modern, full-stack face recognition attendance platform built with **Flask**, **OpenCV**, and **face_recognition**, wrapped in a premium light-theme AI dashboard UI (glassmorphism, smooth animations, live camera recognition, charts, and reports).

---

## 1. Features

- **Admin login** with hashed passwords and session-based auth
- **Live face recognition** through the browser webcam, with bounding-box overlay, confidence score, and known/unknown states
- **Step-by-step registration wizard** — personal details → multi-sample face capture with a live quality meter → confirmation
- **People management** — searchable/filterable grid, profile pages, edit, delete
- **Automatic attendance** — entry/exit tracking, duplicate-prevention per day, Present/Late status, duration calculation
- **Unknown face detection** — snapshots, confidence, detection-count, cooldown de-duplication so the same stranger isn't logged hundreds of times
- **Recognition history timeline** with filters (known/unknown/date/person)
- **Reports** — attendance trend, known-vs-unknown, department breakdown, top people, hourly activity, plus **CSV / Excel / PDF** export
- **Settings** — recognition threshold & sensitivity sliders, camera config, password change, database backup, destructive-action confirmations
- **Global search**, toast notifications, responsive sidebar (collapses to hamburger on mobile)

---

## 2. Technology Stack

| Layer | Tech |
|---|---|
| Backend | Python 3, Flask |
| Face detection/recognition | OpenCV, `face_recognition` (dlib) |
| Database | SQLite |
| Frontend | HTML5, CSS3 (custom design system), vanilla JavaScript |
| Charts | Chart.js (CDN) |
| Exports | openpyxl (Excel), reportlab (PDF) |

---

## 3. Folder Structure

```text
face_recognition_system/
│
├── app.py                 # Flask app: routes, API endpoints, recognition pipeline
├── database.py             # SQLite schema, connection helpers, settings
├── face_utils.py           # Face detection/encoding/comparison helpers (OpenCV + face_recognition)
├── requirements.txt
├── database.db              # Created automatically on first run
│
├── templates/
│   ├── base.html            # Shared sidebar/topbar shell
│   ├── login.html
│   ├── dashboard.html
│   ├── register.html
│   ├── recognition.html
│   ├── people.html
│   ├── person_details.html
│   ├── attendance.html
│   ├── history.html
│   ├── unknown_faces.html
│   ├── reports.html
│   └── settings.html
│
└── static/
    ├── css/style.css
    ├── js/script.js
    └── face_data/
        ├── profiles/        # Saved profile photos from registration
        └── unknown/         # Unknown-face snapshots
```

---

## 4. Installation

### 4.1 Requirements

- **Python 3.9 – 3.11** recommended (dlib wheels are most readily available for these versions)
- A working C++ build toolchain if pip has to compile `dlib` from source (see Troubleshooting)
- A webcam (accessed through the browser — no server-side camera drivers required)

### 4.2 Setup

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

The first run automatically creates `database.db` with all required tables and a demo admin account.

### 4.3 Open the app

Go to **http://127.0.0.1:5000** in your browser. Chrome, Edge, or Firefox recommended (camera access requires `localhost` or HTTPS).

### 4.4 Demo login credentials

```
Username: admin
Password: admin123
```

Change this immediately from **Settings → Security** in a real deployment.

---

## 5. How to Register a Person

1. Go to **Register Person** in the sidebar.
2. **Step 1** — enter their full name (required) and any other details you have. Check the consent box confirming you have permission to store their face data.
3. **Step 2** — click **Enable Camera**, then either click **Capture Sample** five times (following the on-screen prompts to turn slightly left/right) or use **Auto-Capture 5** to do it automatically. Each capture shows a live quality score; low-quality captures (poor lighting, no face, multiple faces) are rejected with an explanation.
4. **Step 3** — confirms the registration and shows a link to the new profile.

## 6. How Face Recognition Works

1. The browser captures a frame from the webcam every ~2 seconds and sends it to `/api/recognize` as a base64 JPEG.
2. The server detects faces with `face_recognition` (HOG-based detector) and computes a 128-dimension encoding per face.
3. Each encoding is compared against every stored encoding using Euclidean distance (`face_recognition.face_distance`). The closest match becomes the candidate identity, and `confidence % = (1 - distance) * 100`.
4. If confidence is **above the configured threshold** (Settings → Recognition Threshold, default 55%), the face is marked **known**: attendance is marked (once per day; later sightings only update the exit time) and the event is logged to Recognition History.
5. If confidence is **below the threshold**, the face is logged as **unknown**, a snapshot is saved, and a short cooldown prevents the same stranger from generating dozens of duplicate records within a short window.

Frames are downscaled before processing and detection runs at a fixed interval (not on every video frame) to keep the UI smooth.

## 7. Database

SQLite tables (see `database.py` for full schema):

- `users` — admin accounts (hashed passwords)
- `persons` — registered people and their profile fields
- `face_encodings` — one or more 128-d face encodings per person, stored as binary blobs
- `attendance` — one row per person per day, with entry/exit times and status
- `recognition_history` — every recognition event, known or unknown
- `unknown_faces` — de-duplicated unknown-face snapshots with detection counts
- `settings` — key/value store for recognition threshold, camera config, etc.

Face embeddings (not raw images) are what recognition actually compares — this is faster and more robust to lighting/angle changes than raw pixel comparison. The best-quality captured photo is also kept as a profile picture for display purposes only.

## 8. Troubleshooting

**`ModuleNotFoundError: No module named 'face_recognition'` or dlib install fails**
`dlib` requires a C++ compiler (CMake + a C++17-capable compiler). Fastest path:
- **Windows:** `pip install cmake` then `pip install dlib`, or install a prebuilt wheel matching your Python version.
- **macOS:** `brew install cmake` first, then `pip install dlib`.
- **Linux:** `sudo apt-get install build-essential cmake` first, then `pip install dlib`.
If installation still fails, the app will still run — every page loads normally, but face capture/recognition endpoints return a clear "engine unavailable" message instead of crashing.

**Camera unavailable / permission denied**
Make sure no other application is using the webcam, and that you allowed camera access when the browser prompted. The app must be accessed via `http://127.0.0.1:5000` or `https://` — camera access is blocked on plain HTTP for non-localhost hosts.

**No face detected during capture**
Improve lighting, face the camera directly, and make sure only one person is in frame.

**Multiple faces detected during capture**
Only one person should be in frame during registration capture.

**Duplicate registration**
The system does not block duplicate names, but each person gets a unique internal ID — use a unique Student/Employee ID per person to avoid confusion in reports.

**openpyxl / reportlab not installed**
Excel and PDF export require these optional packages (already listed in `requirements.txt`). If missing, those two export buttons return a clear error asking you to install them; CSV export has no extra dependency.

---

## 9. Security Notes

- Passwords are hashed with Werkzeug's `generate_password_hash` / `check_password_hash` — never stored in plain text.
- All pages and API routes (except `/login`) require an authenticated session.
- Registration requires an explicit consent checkbox before any face data is stored.
- Deleting a person cascades to their face encodings, and destructive actions in Settings (clearing unknown faces, deleting all face data) require confirmation dialogs.
- `app.secret_key` in `app.py` is a placeholder — set a strong, random value via an environment variable before any real deployment.

---

## 10. Notes for Presentation / Demo

- The dashboard, people grid, attendance, history, and reports all work immediately with sample data you create through the UI — no seed data is included.
- If you don't have `dlib`/`face_recognition` installed in time for a demo, the entire UI, database, attendance logic, and reports still function — only the actual camera-based detection is disabled, with a clear on-screen indicator on the Dashboard's System Status card.
