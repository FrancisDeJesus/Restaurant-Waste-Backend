# Restaurant Waste Backend

Django REST API backend for the Restaurant Waste Management System.

## Overview

This backend provides APIs for:

- Accounts and authentication (including JWT)
- Employee management
- Trash pickup workflows
- Donation drive operations
- Food menu management
- Rewards and subscriptions
- Driver-related features
- Analytics endpoints

## Tech Stack

- Python
- Django
- Django REST Framework
- Simple JWT
- django-cors-headers
- Firebase Admin SDK (for Google/Firebase auth integration)
- SQLite (default development database)

## Prerequisites

- Python 3.10+ (recommended)
- pip
- Virtual environment support (`venv`)

## Getting Started

1. Create and activate a virtual environment.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install required packages:

```bash
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers firebase-admin
```

3. Apply migrations:

```bash
python manage.py migrate
```

4. Start development server:

```bash
python manage.py runserver 0.0.0.0:8000
```

Server default URL:

- `http://127.0.0.1:8000`

## API Routes (Top-Level)

Defined in `restaurant_backend/urls.py`:

- `api/accounts/`
- `api/employees/`
- `api/food_menu/`
- `api/rewards/`
- `api/analytics/`
- `api/subscriptions/`
- `api/token/`
- `api/token/refresh/`
- plus other app routes under `api/`

## Firebase Admin Setup

Current config in `accounts/firebase_config.py` expects this file:

- `accounts/restaurant-waste-app-75ce6-firebase-adminsdk-fbsvc-ac4725dca3.json`

Important:

- Use your own Firebase service account key for your environment.
- Never commit sensitive credentials in public repositories.

## CORS and Auth Notes

- `CORS_ALLOW_ALL_ORIGINS = True` is enabled for development.
- JWT authentication is configured via Simple JWT.

For production, tighten CORS and security settings.

## Useful Commands

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py test
```

## Project Structure

```text
restaurant_backend/
  settings.py
  urls.py
accounts/
employees/
trash_pickups/
rewards/
donation_drive/
food_menu/
analytics/
drivers/
subscriptions/
manage.py
db.sqlite3
```

## Troubleshooting

- `ModuleNotFoundError`:
  - Ensure virtual environment is activated.
  - Re-run dependency install command.
- Frontend cannot connect:
  - Confirm server is running on port `8000`.
  - If testing on phone, use host machine IP and same network.
- Auth issues:
  - Check JWT token endpoints and token expiration settings in `settings.py`.
- `OperationalError` on trash pickup APIs:
  - Run `python manage.py migrate trash_pickups`.
  - Ensure migrations `0007` and `0008` are applied in the active DB.

## Team Notes

- Keep this README updated when dependencies or endpoint structure changes.
- Consider adding a pinned `requirements.txt` for reproducible setup.
