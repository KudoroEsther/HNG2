# Profile Intelligence Service

A REST API that enriches a name with gender, age, and nationality data by aggregating three free external APIs, then stores and manages the results.

---

## Tech Stack

- **FastAPI** — web framework
- **PostgreSQL** — database
- **SQLAlchemy** — table definitions and schema creation
- **databases** — async database queries
- **httpx** — async HTTP calls to external APIs
- **uuid-extensions** — UUID v7 ID generation

---

## External APIs Used

| API | Data Extracted |
|---|---|
| [Genderize](https://api.genderize.io) | gender, gender_probability, sample_size |
| [Agify](https://api.agify.io) | age, age_group |
| [Nationalize](https://api.nationalize.io) | country_id, country_probability |

No API keys required.

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/profiles` | Create a new profile by name |
| `GET` | `/api/profiles` | List all profiles (filterable) |
| `GET` | `/api/profiles/{id}` | Get a single profile by ID |
| `DELETE` | `/api/profiles/{id}` | Delete a profile |

### POST /api/profiles
```json
// Request
{ "name": "ella" }

// Response 201
{
  "status": "success",
  "data": {
    "id": "uuid-v7",
    "name": "ella",
    "gender": "female",
    "gender_probability": 0.99,
    "sample_size": 1234,
    "age": 46,
    "age_group": "adult",
    "country_id": "US",
    "country_probability": 0.85,
    "created_at": "2026-04-17T12:00:00Z"
  }
}
```
Submitting the same name again returns the existing profile with `"message": "Profile already exists"`.

### GET /api/profiles
Supports optional case-insensitive query filters:
```
/api/profiles?gender=female&country_id=NG&age_group=adult
```

---

## Age Groups

| Range | Group |
|---|---|
| 0–12 | child |
| 13–19 | teenager |
| 20–59 | adult |
| 60+ | senior |

---

## Local Setup

**1. Clone and install dependencies**
```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
pip install -r requirements.txt
```

**2. Create a `.env` file**
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/profiles_db
```
> To use Railway's hosted Postgres instead, copy the URL from your Railway project → Postgres service → Connect tab.

**3. Run the server**
```bash
uvicorn main:app --reload
```

The app auto-creates the `profiles` table on startup — no migrations needed.

---

## Deployment (Railway)

1. Push code to GitHub
2. Create a new Railway project → **Deploy from GitHub repo**
3. Add a **PostgreSQL** service from the Railway dashboard
4. In your app service → **Variables** tab → link `DATABASE_URL` from the Postgres service
5. Railway uses the `Procfile` to start the server automatically

---

## Error Responses

| Status | Reason |
|---|---|
| 400 | Missing or empty name |
| 422 | Invalid input type |
| 404 | Profile not found |
| 502 | External API returned invalid data |
