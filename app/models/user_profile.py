from sqlalchemy import Column, String, JSON, Boolean
from app.database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(String, primary_key=True, index=True)

    subjects = Column(JSON, default=[])
    grades = Column(JSON, default=[])

    curriculum = Column(String, default="CSEC")

    learning_preferences = Column(JSON, default={
        "visual": True,
        "auditory": True,
        "kinesthetic": True
    })

    mixed_ability = Column(Boolean, default=True)