# Application Portal

A secure document collection portal for education consultancy applications.

## Features
- Student signup/login with a single application profile.
- Course-driven document checklist and required details.
- Multi-session uploads with status tracking and version history.
- Admin dashboard for review, ZIP download, and CSV export.

## Local Development

### 1) Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Database + Seed Data
```bash
python manage.py migrate
```
The migration seeds course templates for Medicine, Engineering, and Master Program.

### 3) Create Admin
```bash
python manage.py createsuperuser
```
Mark staff users as `is_staff=True` to access the admin dashboard.

### 4) Run
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/`.

## Tests
```bash
python manage.py test
```

## Environment Variables
- `DJANGO_SECRET_KEY`: Django secret key.
- `DJANGO_DEBUG`: `true` or `false`.
- `DJANGO_ALLOWED_HOSTS`: Comma-separated hosts.
- `DJANGO_CSRF_SECURE`: `true` to enforce secure CSRF cookies.
- `DJANGO_SESSION_SECURE`: `true` to enforce secure session cookies.
- `DJANGO_HSTS_SECONDS`: integer for HSTS max age.
- `DJANGO_HSTS_INCLUDE_SUBDOMAINS`: `true`/`false`.
- `DJANGO_HSTS_PRELOAD`: `true`/`false`.
