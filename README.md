# Application Portal

A secure web application for education consultancies to collect, review, and track student application documents.

## Features
- Student authentication and single application profile.
- Course-template driven detail fields and document checklist.
- Multi-session uploads with validation, status tracking, and versioning.
- Strict server-side file renaming format.
- Staff review workflow with notes, ZIP download, and CSV export.
- Audit logging for uploads, reviews, and exports.

## Run Locally (Python)

### 1) Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Migrate + seed
```bash
python manage.py migrate
```

### 3) Create staff user
```bash
python manage.py createsuperuser
```

### 4) Start web app (network-accessible)
```bash
python manage.py runserver 0.0.0.0:8000
```
Open: `http://localhost:8000`.

## Run with Docker (Production-like)
```bash
docker compose up --build
```
Open: `http://localhost:8000`.

## Tests
```bash
python manage.py test
```

## Environment Variables
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DJANGO_CSRF_SECURE`
- `DJANGO_SESSION_SECURE`
- `DJANGO_HSTS_SECONDS`
- `DJANGO_HSTS_INCLUDE_SUBDOMAINS`
- `DJANGO_HSTS_PRELOAD`
- `DJANGO_SUPERUSER_USERNAME` (Docker entrypoint)
- `DJANGO_SUPERUSER_EMAIL` (Docker entrypoint)
- `DJANGO_SUPERUSER_PASSWORD` (Docker entrypoint)
