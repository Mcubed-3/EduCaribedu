from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_profile import UserProfile

router = APIRouter(prefix="/api/profile", tags=["Profile"])


@router.post("/setup")
def setup_profile(payload: dict, db: Session = Depends(get_db)):
    user_id = payload.get("user_id")

    profile = db.query(UserProfile).filter_by(user_id=user_id).first()

    if not profile:
        profile = UserProfile(user_id=user_id)

    profile.subjects = payload.get("subjects", [])
    profile.grades = payload.get("grades", [])
    profile.curriculum = payload.get("curriculum", "CSEC")

    db.add(profile)
    db.commit()

    return {"status": "saved"}