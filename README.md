# Restaurant Waste Backend

Django REST API backend for the Restaurant Waste Management System.

## Project Description

The Restaurant Waste Management System is a mobile and web-based platform designed
to support restaurants in Davao City in managing food waste collection,
segregation, and reporting. Through this backend, the platform provides secure
API services for waste pickup requests, waste validation workflows, account and
role management, and analytics data processing.

This backend serves as the central service layer that powers the frontend app,
driver operations, and analytics modules.

## Core Features

- Secure authentication and account services
- Waste pickup request and status management
- Food menu and donation drive modules
- Driver-related pickup coordination endpoints
- Rewards and subscription services
- Analytics endpoints for waste monitoring

## Trash Pickup Weight Model

Trash pickup records support three related weight fields:

- `estimated_weight_kg`: restaurant-side estimate at request time
- `actual_weight_kg`: measured value (typically set at form submit or completion)
- `weight_kg`: legacy compatibility field

Effective weight resolution order used by backend services:

1. `actual_weight_kg`
2. `estimated_weight_kg`
3. `weight_kg`

This fallback logic is used in serializers and analytics aggregation so existing clients remain compatible while newer clients can submit both estimated and actual values.

## Trash Pickup API Notes

For `trash_pickups` create/update payloads:

- send `estimated_weight_kg` (required on create)
- send `actual_weight_kg` when available
- `weight_kg` is still accepted for backward compatibility

When completing a pickup (`PATCH /api/trash_pickups/{id}/complete/`), you can include `actual_weight_kg` to overwrite the effective measured weight used by analytics and downstream modules.

### Quick API Request/Response Examples

Use these examples for manual testing (Postman, curl, or REST client).

`POST /api/trash_pickups/` (create pickup with estimated weight)

```http
POST /api/trash_pickups/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "waste_type": "food",
  "estimated_weight_kg": 12.5,
  "schedule_date": "2026-03-12T10:00:00Z"
}
```

Sample `201 Created` response:

```json
{
  "message": "Pickup created successfully and is now visible to drivers.",
  "pickup": {
    "id": 41,
    "waste_type": "food",
    "waste_type_display": "Food Waste",
    "weight_kg": "12.5",
    "estimated_weight_kg": "12.5",
    "actual_weight_kg": null,
    "status": "pending"
  }
}
```

`PATCH /api/trash_pickups/{id}/complete/` (driver submits measured weight)

```http
PATCH /api/trash_pickups/41/complete/
Authorization: Bearer <driver_access_token>
Content-Type: application/json

{
  "actual_weight_kg": 11.8
}
```

Sample `200 OK` response:

```json
{
  "message": "Pickup #41 completed! 🎉 11 points awarded.",
  "points_awarded": 11
}
```

Note: Analytics and totals resolve weight in this order: `actual_weight_kg` -> `estimated_weight_kg` -> `weight_kg`.

## System Architecture

Client Applications (Flutter Mobile/Web)
-> REST API Layer (Django REST Framework)
-> Domain Modules (accounts, pickups, donations, rewards, analytics)
-> Database (SQLite for development; configurable for production)

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

## Thesis API Validation Checklist

Run this quick pass before demo day.

- [ ] `python manage.py migrate` completed without errors
- [ ] Auth token retrieval works via `POST /api/token/`
- [ ] Pickup create works via `POST /api/trash_pickups/` with `estimated_weight_kg`
- [ ] Pickup complete works via `PATCH /api/trash_pickups/{id}/complete/` with `actual_weight_kg`
- [ ] Analytics endpoint returns updated totals after completion

Expected behavior:

- Effective weight priority is `actual_weight_kg` -> `estimated_weight_kg` -> `weight_kg`
- Legacy clients that still send `weight_kg` remain compatible
