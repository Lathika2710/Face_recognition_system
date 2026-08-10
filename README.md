# FaceAI — AI Face Recognition & Smart Attendance System

A Flask-based face recognition attendance system with login/signup, per-user data isolation, live webcam recognition, attendance tracking, and admin report dashboards.

---

## Features

- **Login / Signup** with hashed passwords and session-based auth
- **Per-user data separation** so each account sees only its own people, attendance, history, and unknown face records
- **Live face recognition** from browser webcam frames
- **Person registration** with profile fields and face sample capture
- **Automatic attendance** logging with daily entry/exit updates and Present/Late status
- **Unknown face detection** with snapshots, counts, cooldown de-duplication, and manual resolution
- **Recognition history** filtered by known/unknown/date/person
- **Reports** with attendance trend, known vs unknown, department stats, top people, hourly activity, plus CSV/Excel/PDF export
- **Settings** for recognition threshold, camera options, session timeout, password change, database backup, and cleanup actions

---

## Technology Stack

| Layer | Tech |
|---|---|
| Backend | Python 3, Flask |
| Face recognition | OpenCV, `face_recognition`, `dlib` |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Exports | `openpyxl`, `reportlab` |

---

## Project Structure

```text
face_recognition_system/
├── app.py
├── database.py
├── face_utils.py
├── requirements.txt
├── README.md
├── database.db
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   ├── recognition.html
│   ├── register.html
│   ├── people.html
│   ├── person_details.html
│   ├── attendance.html
│   ├── history.html
│   ├── unknown_faces.html
│   ├── reports.html
│   └── settings.html
└── static/
    ├── css/style.css
    ├── js/script.js
    └── face_data/
        ├── profiles/
        └── unknown/
```

---

## Installation

### Requirements

- Python 3.9–3.11 recommended
- `face_recognition`, `dlib`, and `opencv-python`
- A webcam for live browser capture

### Setup

```powershell
cd c:\Users\KiTE\Desktop\face_recognition_system
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The first run creates `database.db` and seeds a default admin user if no users exist.

### Open the App

Visit: `http://127.0.0.1:5000`

---

## Default Login

```
Username: admin
Password: admin123
```

Use this default account only for initial access, then create a new user or change the password.

---

## How to Use

### Signup and Login

- Open the app and use the login page.
- If you do not have an account, click the signup link to create one.
- After signup, log in with your new credentials.

### Register a Person

1. Go to **Register** in the sidebar.
2. Enter the person’s details and accept consent.
3. Capture face samples from your webcam.
4. Save the person profile.

### Recognition and Attendance

- Open **Recognition** to start live face matching.
- Known faces are logged and attendance is updated.
- Unknown faces are saved as snapshots for review.

---

## Database Schema

Key tables:

- `users` — admin accounts
- `persons` — registered people with `user_id`
- `face_encodings` — face embeddings linked to persons
- `attendance` — entry/exit per person per day
- `recognition_history` — known/unknown recognition logs per user
- `unknown_faces` — unrecognized face snapshots scoped by user
- `settings` — app configuration values

User-owned data is enforced in the backend so accounts do not see other users’ people or recognition data.

---

## Troubleshooting

### face_recognition install fails
Install a C++ toolchain and `cmake` first, then retry:

```powershell
pip install cmake
pip install dlib
pip install face_recognition
```

### Browser camera access issues
- Use `http://127.0.0.1:5000`
- Allow camera permission in the browser
- Close any other app using the webcam

### Optional export support
- Excel export uses `openpyxl`
- PDF export uses `reportlab`

If they are missing, installs are simple:

```powershell
pip install openpyxl reportlab
```

---

## Notes

- `app.secret_key` in `app.py` is currently a placeholder. Replace it before deploying.
- The system is designed for local/demo use; secure production deployment requires HTTPS and a stronger secret.
- Data is kept separate per user account once you log in.

