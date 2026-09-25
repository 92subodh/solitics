# College ERP API

A Django REST API starter based on the supplied architecture. It has JWT authentication, role-aware accounts, academic structure/enrolment, attendance, fees, library, and notices. SQLite is the default for local development; PostgreSQL is ready through `DATABASE_URL` and Docker Compose.

## Start locally

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Use `POST /api/auth/login/` with `username` and `password` to get a JWT pair. Send `Authorization: Bearer <access-token>` to protected endpoints.

## API surface

`/api/users/`, `/api/departments/`, `/api/courses/`, `/api/subjects/`, `/api/enrollments/`, `/api/attendance/`, `/api/fee-structures/`, `/api/payments/`, `/api/books/`, `/api/loans/`, and `/api/notices/`.

Administrators can mutate resources; authenticated users can read them. Django admin is at `/admin/`.
