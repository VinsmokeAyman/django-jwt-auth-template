# Django JWT backend template

A reusable Django REST Framework backend with JWT authentication, HTTP-only refresh cookies, token rotation, logout, and role-based permissions. Authentication uses Simple JWT and the custom `users.User` model.

## Local setup

Create a Python environment and install the dependencies pinned in `requirements.txt`. The original project environment used Python 3.13.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

On macOS/Linux, activate the environment with `source .venv/bin/activate` instead.

- API base URL: `http://localhost:8000/api/users/`
- Django admin: `http://localhost:8000/admin/`

The database is SQLite. Apply all included migrations in order; the latest users migration removes the former company and organization models and relationships.

To use the protected API endpoints, sign in to Django admin with your superuser and set that user's `role` to `admin`. Django's `is_staff` and `is_superuser` flags do not satisfy the API's role check by themselves.

## User model and permissions

`User` extends Django's `AbstractUser` with a unique email address, a `role`, and optional `phone` and `fullName` fields. Available roles are `admin`, `tier1`, `tier2`, and `tier3`; new users default to `tier3`.

The permission class named `IsCompanyAdmin` checks only that the user is authenticated and has `role == "admin"`. No company or organization association is required. `IsTier1` checks for the `tier1` role and is not applied to the current endpoints.

`UserSerializer` exposes the model fields with the password marked write-only and the ID read-only. The user-creation view calls `create_user` directly rather than validating input through this serializer.

## API endpoints

| Method | Path | Access | Behavior |
| --- | --- | --- | --- |
| GET | `/api/users/test/` | Public | Returns an API status message. |
| POST | `/api/users/login/` | Public, throttled | Returns an access token and user data; sets a refresh cookie. |
| POST | `/api/users/refresh/` | Refresh cookie | Replaces the refresh token and returns a new access token. |
| POST | `/api/users/logout/` | Public | Blacklists the refresh token when valid and clears its cookie. |
| POST | `/api/users/verify-admin/` | Admin role | Returns an admin confirmation and user data. |
| POST | `/api/users/create/` | Admin role | Creates a user with the default `tier3` role. |

### Login

Send JSON to `POST /api/users/login/`:

```json
{
  "username": "your-username-or-email",
  "password": "your-password",
  "rememberMe": true
}
```

`username` and `password` are required. `rememberMe` is optional and defaults to `false`.

A successful response contains `message`, `access`, and `user`. The refresh token is set in the `refresh_token` cookie. Missing credentials return HTTP 400; invalid credentials return HTTP 401.

### Create a user

Send an admin access token and JSON to `POST /api/users/create/`:

```json
{
  "username": "new-user",
  "email": "new-user@example.com",
  "password": "your-password",
  "phone_number": "+212600000000",
  "fullName": "New User"
}
```

All five fields are required by this endpoint, including phone and full name. The request field `phone_number` is stored as `phone`. No company, organization, or role field is needed. The endpoint returns HTTP 201 with a success message, or HTTP 400 for missing fields, a duplicate username, or a duplicate email address.

### Refresh and logout

Send `POST /api/users/refresh/` with the refresh cookie. No JSON body is required. On success, the endpoint blacklists the old refresh token, sets a replacement cookie, and returns an `access` token. A missing, invalid, or expired refresh token returns HTTP 401.

Send `POST /api/users/logout/` with the refresh cookie to blacklist it and clear the cookie. The endpoint also returns a success message if the cookie is missing or contains an invalid token. Existing access tokens remain valid until they expire.

## Frontend integration

Send access tokens to protected endpoints using:

```http
Authorization: Bearer <access-token>
```

Use `credentials: "include"` for login, refresh, and logout so the browser receives and sends the HTTP-only refresh cookie.

```javascript
const response = await fetch("http://localhost:8000/api/users/login/", {
  method: "POST",
  credentials: "include",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    username: "your-username",
    password: "your-password",
    rememberMe: true,
  }),
});
const data = await response.json();
if (!response.ok) throw new Error(data.error ?? "Login failed");
const accessToken = data.access;
```

The current CORS configuration allows `http://localhost:5173` and `http://127.0.0.1:5173`, with credentials enabled. Use matching frontend and backend hostnames during local development with the existing `SameSite=Lax` cookie setting.

## Current configuration

| Setting | Value |
| --- | --- |
| Access-token lifetime | 15 minutes |
| Refresh-token lifetime | 7 days |
| Refresh cookie | `refresh_token`, HTTP-only, `SameSite=Lax`, path `/` |
| Cookie persistence | 7 days when `rememberMe` is true; otherwise a session cookie |
| Login throttle | `AnonRateThrottle` with scope `login` and configured rate `5/minutes` |
| Database | SQLite (`db.sqlite3`) |

Settings live in `config/settings.py`; refresh-cookie options live in `users/views.py`. There is no `.env` loader. The current development configuration has a hardcoded development secret key, `DEBUG=True`, an empty `ALLOWED_HOSTS` list, and cookies with `secure=False`. Configure these values and frontend origins for your own deployment, using a private secret key.

## Users app layout

| File | Purpose |
| --- | --- |
| `models.py` | Custom user model and role choices. |
| `serializers.py` | User serialization. |
| `views.py` | API status, user creation, login, refresh, admin verification, and logout. |
| `urls.py` | Users API routes. |
| `permissions.py` | Admin and tier-one role checks. |
| `throttles.py` | Login throttle class. |
| `admin.py` | User registration in Django admin. |
| `apps.py` | App configuration. |
| `migrations/` | Schema history, including removal of company and organization data structures. |
| `tests.py` | Test placeholder; no application tests are implemented. |

## Sharing the template

Include the source, migrations, `requirements.txt`, README, and `.gitignore` in the repository. Local environments, SQLite databases, and `.env` files are excluded by `.gitignore`. Keep the migration history so a fresh database can be created with `python manage.py migrate`.
