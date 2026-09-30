from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import DateTime, Float, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fitbuddy.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(120))
    age: Mapped[int] = mapped_column(Integer)
    weight: Mapped[float] = mapped_column(Float)
    goal: Mapped[str] = mapped_column(String(120))
    intensity: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    original_plan: Mapped[str] = mapped_column(Text)
    updated_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nutrition_tip: Mapped[str] = mapped_column(Text)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    return SessionLocal()


def save_user(
    username: str,
    user_id: str,
    age: int,
    weight: float,
    goal: str,
    intensity: str,
) -> User:
    with get_session() as db:
        existing = db.scalar(select(User).where(User.user_id == user_id))
        if existing:
            existing.username = username
            existing.age = age
            existing.weight = weight
            existing.goal = goal
            existing.intensity = intensity
            db.commit()
            db.refresh(existing)
            return existing

        user = User(
            username=username,
            user_id=user_id,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def get_user(user_id: str) -> Optional[User]:
    with get_session() as db:
        return db.scalar(select(User).where(User.user_id == user_id))


def save_plan(user_id: str, original_plan: str, nutrition_tip: str) -> Plan:
    with get_session() as db:
        plan = Plan(
            user_id=user_id,
            original_plan=original_plan,
            nutrition_tip=nutrition_tip,
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan


def get_original_plan(user_id: str) -> Optional[Plan]:
    with get_session() as db:
        return db.scalar(
            select(Plan)
            .where(Plan.user_id == user_id)
            .order_by(Plan.id.desc())
        )


def update_plan(user_id: str, updated_plan: str, feedback: str) -> Optional[Plan]:
    with get_session() as db:
        plan = db.scalar(
            select(Plan)
            .where(Plan.user_id == user_id)
            .order_by(Plan.id.desc())
        )
        if not plan:
            return None
        plan.updated_plan = updated_plan
        plan.feedback = feedback
        db.commit()
        db.refresh(plan)
        return plan


def get_all_users() -> list[User]:
    with get_session() as db:
        return list(db.scalars(select(User).order_by(User.created_at.desc())).all())


def get_all_plans() -> list[Plan]:
    with get_session() as db:
        return list(db.scalars(select(Plan).order_by(Plan.created_at.desc())).all())


def delete_user(user_id: str) -> bool:
    with get_session() as db:
        user = db.scalar(select(User).where(User.user_id == user_id))
        if not user:
            return False

        plans = list(db.scalars(select(Plan).where(Plan.user_id == user_id)).all())
        for plan in plans:
            db.delete(plan)
        db.delete(user)
        db.commit()
        return True
