from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import uuid
from datetime import datetime

from database import engine, SessionLocal
from models import Base, Profile

app = FastAPI()

Base.metadata.create_all(bind=engine)


# -------------------------
# REQUEST MODEL
# -------------------------
class NameRequest(BaseModel):
    name: str


# -------------------------
# CREATE PROFILE
# -------------------------
@app.post("/api/profiles")
def create_profile(data: NameRequest):

    db = SessionLocal()
    name = data.name.lower().strip()

    # check if exists
    existing = db.query(Profile).filter(Profile.name == name).first()

    if existing:
        return {
            "status": "success",
            "message": "Profile already exists",
            "data": {
                "id": existing.id,
                "name": existing.name,
                "gender": existing.gender,
                "age": existing.age,
                "age_group": existing.age_group,
                "country_id": existing.country_id,
                "created_at": existing.created_at
            }
        }

    # external APIs
    gender = requests.get(f"https://api.genderize.io?name={name}").json()
    age = requests.get(f"https://api.agify.io?name={name}").json()
    nat = requests.get(f"https://api.nationalize.io?name={name}").json()

    # validation
    if not gender.get("gender"):
        raise HTTPException(status_code=502, detail="Gender API failed")

    if not age.get("age"):
        raise HTTPException(status_code=502, detail="Age API failed")

    if not nat.get("country"):
        raise HTTPException(status_code=502, detail="Nationality API failed")

    # age group logic
    age_value = age["age"]

    if age_value <= 12:
        age_group = "child"
    elif age_value <= 19:
        age_group = "teenager"
    elif age_value <= 59:
        age_group = "adult"
    else:
        age_group = "senior"

    country = nat["country"][0]

    # save to DB
    profile = Profile(
        id=str(uuid.uuid4()),
        name=name,
        gender=gender["gender"],
        gender_probability=gender["probability"],
        sample_size=gender["count"],
        age=age_value,
        age_group=age_group,
        country_id=country["country_id"],
        country_probability=country["probability"],
        created_at=datetime.utcnow().isoformat()
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {
        "status": "success",
        "data": {
            "id": profile.id,
            "name": profile.name,
            "gender": profile.gender,
            "gender_probability": profile.gender_probability,
            "sample_size": profile.sample_size,
            "age": profile.age,
            "age_group": profile.age_group,
            "country_id": profile.country_id,
            "country_probability": profile.country_probability,
            "created_at": profile.created_at
        }
    }


# -------------------------
# GET SINGLE PROFILE
# -------------------------
@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: str):

    db = SessionLocal()

    profile = db.query(Profile).filter(Profile.id == profile_id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "status": "success",
        "data": {
            "id": profile.id,
            "name": profile.name,
            "gender": profile.gender,
            "gender_probability": profile.gender_probability,
            "sample_size": profile.sample_size,
            "age": profile.age,
            "age_group": profile.age_group,
            "country_id": profile.country_id,
            "country_probability": profile.country_probability,
            "created_at": profile.created_at
	    
        }
    }


# -------------------------
# GET ALL PROFILES (WITH FILTERS)
# -------------------------
@app.get("/api/profiles")
def get_all_profiles(gender: str = None, country_id: str = None, age_group: str = None):

    db = SessionLocal()

    query = db.query(Profile)

    if gender:
        query = query.filter(Profile.gender == gender.lower())

    if country_id:
        query = query.filter(Profile.country_id == country_id.upper())

    if age_group:
        query = query.filter(Profile.age_group == age_group.lower())

    profiles = query.all()

    result = []

    for p in profiles:
        result.append({
            "id": p.id,
            "name": p.name,
            "gender": p.gender,
            "age": p.age,
            "age_group": p.age_group,
            "country_id": p.country_id
        })

    return {
        "status": "success",
        "count": len(result),
        "data": result
    }
@app.get("/")
def root():
    return {
        "status": "success",
        "message": "API is running"
    }
@app.get("/health")
def health():
    return {
        "status": "success",
        "message": "healthy"
    }
@app.get("/me")
def me():
    return {
        "name": "Kelani Khadijat",
        "email": "kelanikhadijat41@gmail.com",
        "github": "https://github.com/kehlany"
    }