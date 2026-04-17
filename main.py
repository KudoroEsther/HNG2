from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import httpx
import asyncio

from database import database, engine, metadata
from models import profiles
from schemas import ProfileRequest
# from uuid_extensions import uuid7str
import uuid


# ── App lifecycle ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    metadata.create_all(engine)   # create tables on startup
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ── Validation error handler (422) ────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = exc.errors()
    # Surface the first meaningful message
    first = errors[0] if errors else {}
    msg = first.get("msg", "Invalid input")
    # Pydantic v2 prefixes with "Value error, " – strip it for cleanliness
    msg = msg.replace("Value error, ", "")
    # Decide status code: empty/missing name → 400, wrong type → 422
    status_code = 400 if "empty" in msg or "missing" in msg.lower() else 422
    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "message": msg},
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_age_group(age: int) -> str:
    if age <= 12:
        return "child"
    elif age <= 19:
        return "teenager"
    elif age <= 59:
        return "adult"
    else:
        return "senior"


def error_502(api_name: str):
    return JSONResponse(
        status_code=502,
        content={"status": "502", "message": f"{api_name} returned an invalid response"},
    )


def profile_dict(row) -> dict:
    return dict(row)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/api/profiles")
async def create_profile(payload: ProfileRequest):
    name = payload.name  # already stripped + lowercased by validator

    # Idempotency check
    existing = await database.fetch_one(profiles.select().where(profiles.c.name == name))
    if existing:
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Profile already exists",
                "data": profile_dict(existing),
            },
        )

    # Call all 3 external APIs concurrently
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            genderize_res, agify_res, nationalize_res = await asyncio.gather(
                client.get(f"https://api.genderize.io?name={name}"),
                client.get(f"https://api.agify.io?name={name}"),
                client.get(f"https://api.nationalize.io?name={name}"),
            )
            genderize   = genderize_res.json()
            agify       = agify_res.json()
            nationalize = nationalize_res.json()
        except Exception:
            return JSONResponse(
                status_code=502,
                content={"status": "error", "message": "Upstream service failure"},
            )

    # Validate Genderize
    if not genderize.get("gender") or genderize.get("count", 0) == 0:
        return error_502("Genderize")

    # Validate Agify
    if agify.get("age") is None:
        return error_502("Agify")

    # Validate Nationalize
    countries = nationalize.get("country", [])
    if not countries:
        return error_502("Nationalize")

    # Process & enrich
    top_country = max(countries, key=lambda c: c["probability"])
    age         = agify["age"]

    data = {
        "id":                 str(uuid.uuid7()),
        "name":               name,
        "gender":             genderize["gender"],
        "gender_probability": genderize["probability"],
        "sample_size":        genderize["count"],
        "age":                age,
        "age_group":          get_age_group(age),
        "country_id":         top_country["country_id"],
        "country_probability": top_country["probability"],
        "created_at":         datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    await database.execute(profiles.insert().values(**data))

    return JSONResponse(status_code=201, content={"status": "success", "data": data})


@app.get("/api/profiles")
async def list_profiles(
    gender:     str | None = Query(default=None),
    country_id: str | None = Query(default=None),
    age_group:  str | None = Query(default=None),
):
    rows = await database.fetch_all(profiles.select())

    result = []
    for row in rows:
        p = profile_dict(row)
        if gender     and p["gender"].lower()     != gender.lower():     continue
        if country_id and p["country_id"].lower() != country_id.lower(): continue
        if age_group  and p["age_group"].lower()  != age_group.lower():  continue
        result.append(p)

    return JSONResponse(
        status_code=200,
        content={"status": "success", "count": len(result), "data": result},
    )


@app.get("/api/profiles/{id}")
async def get_profile(id: str):
    row = await database.fetch_one(profiles.select().where(profiles.c.id == id))
    if not row:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "Profile not found"},
        )
    return JSONResponse(
        status_code=200,
        content={"status": "success", "data": profile_dict(row)},
    )


@app.delete("/api/profiles/{id}")
async def delete_profile(id: str):
    row = await database.fetch_one(profiles.select().where(profiles.c.id == id))
    if not row:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "Profile not found"},
        )
    await database.execute(profiles.delete().where(profiles.c.id == id))
    return Response(status_code=204)
