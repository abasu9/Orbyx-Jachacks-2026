import uuid
from sqlalchemy import Column, Date, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    name = Column(String(255), nullable=False)
    level = Column(Text, nullable=True)
    apr = Column(JSONB, nullable=True)
    pip = Column(Integer, nullable=False, default=0)
    joiningdate = Column(Date, nullable=False)
    gh_username = Column(Text, nullable=True)
    ranking = Column(Float, nullable=True)
    roi = Column(Float, nullable=True)
    report_id = Column(Text, nullable=True)
