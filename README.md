# Macro Tracker API (v2 — Supabase Auth)

FastAPI backend using Supabase Auth natively — no custom user table, no password hashing, no JWT secrets.

---

## Why Supabase Auth?

- Registration, login, password hashing, and JWT signing are all handled by Supabase
- Row Level Security (RLS) ensures users can only access their own data at the database level
- One less thing to maintain and get wrong

---

## Stack

- **FastAPI** — Python web framework
- **Supabase Auth** — authentication (no custom users table)
- **Supabase Postgres** — database with RLS
- **Docker** — deployment

---

## 1. Supabase Setup

1. Go to [supabase.com](https://supabase.com) → create a new project
2. Go to **SQL Editor** → paste and run `schema.sql`
3. Go to **Project Settings → API** and copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon / public** key → `SUPABASE_ANON_KEY`
   - **service_role** key → `SUPABASE_SERVICE_KEY`

> The anon key is safe to expose in the frontend. The service key must stay server-side only.

---

## 2. Local Development

```bash
cd macro-tracker-api

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Fill in SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY

uvicorn app.main:app --reload
```

- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`

---

## 3. Deploy to Railway

1. Push to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variables:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_KEY=your-service-role-key
   ```
4. Railway detects the Dockerfile and deploys automatically
5. Settings → Networking → Generate Domain

---

## 4. Deploy to Render

1. Push to GitHub
2. [render.com](https://render.com) → New Web Service → Connect repo
3. Environment: **Docker**, Port: **8000**
4. Add the same 3 environment variables
5. Deploy

---

## 5. API Reference

### Auth
| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | `{email, password}` | Register via Supabase Auth |
| POST | `/auth/login` | `{email, password}` | Login, returns Supabase JWT |
| POST | `/auth/logout` | — | Sign out |
| GET | `/auth/me` | — | Current user info |

All other endpoints require `Authorization: Bearer <token>` header.

### Goals
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/goals/` | Get goals |
| PUT | `/goals/` | Update goals |

### Food Library
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/library/` | List all foods |
| POST | `/library/` | Add food |
| PUT | `/library/{id}` | Edit food |
| DELETE | `/library/{id}` | Delete food |

### Food Log
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/log/?log_date=YYYY-MM-DD` | Get log for a date (default: today) |
| GET | `/log/history` | Daily summaries |
| POST | `/log/` | Add entry |
| DELETE | `/log/{id}` | Remove entry |

---

## 6. Connecting the Frontend

```javascript
const API_URL = 'https://your-api.railway.app';

// Login
const res = await fetch(`${API_URL}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
const { access_token } = await res.json();
localStorage.setItem('token', access_token);

// Authenticated request
const log = await fetch(`${API_URL}/log/`, {
  headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
}).then(r => r.json());
```
