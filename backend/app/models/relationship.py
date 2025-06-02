# backend/app/models/relationship.py
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLAlchemyEnum, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class RelationshipStatus(Enum):
    """
    Enum representing the status of a relationship.
    """

    ACTIVE = "active"  # 近 7 天内有持续有效对话
    COOLING = "cooling"  # 近 7 天内对话不足但未沉寂
    SILENT = "silent"  # 超过 14 天无有效对话
    BROKEN = "broken"  # 人类主动解绑或 AI 主动休眠


class Relationship(Base):
    """
    Model representing the relationship between an AI and a human.
    """

    __tablename__ = "relationships"

    relationship_id = Column(String, primary_key=True, index=True)
    ai_id = Column(String, nullable=False, index=True)
    human_id = Column(String, nullable=False, index=True)
    init_timestamp = Column(DateTime, nullable=False)
    last_active_time = Column(DateTime, nullable=False)
    interaction_count = Column(Integer, default=0)
    active_days = Column(Integer, default=0)
    status = Column(
        SQLAlchemyEnum(RelationshipStatus), default=RelationshipStatus.ACTIVE
    )
    emotional_resonance_count = Column(Integer, default=0)
    human_affection_score = Column(Float, default=0.0)
    ai_recognition_score = Column(Float, default=0.0)
    first_memory_time: Optional[datetime] = Column(DateTime)
    shared_tag_count = Column(Integer, default=0)
    last_relationship_stage: Optional[int] = Column(Integer, default=1)  # 关系阶段
    is_soulmate_link: Optional[bool] = Column(Boolean, default=False)  # 是否为灵魂伴侣
    manual_disconnection: Optional[bool] = Column(Boolean, default=False)  # 人类是否手动断开
    ai_sleep_triggered: Optional[bool] = Column(Boolean, default=False)  # AI 是否触发休眠

    def to_dict(self) -> dict:
        """
        Convert the Relationship object to a dictionary.

        Returns:
            dict: Dictionary representation of the Relationship object.
        """
        return {
            "relationship_id": self.relationship_id,
            "ai_id": self.ai_id,
            "human_id": self.human_id,
            "init_timestamp": self.init_timestamp.isoformat(),
            "last_active_time": self.last_active_time.isoformat(),
            "interaction_count": self.interaction_count,
            "active_days": self.active_days,
            "status": self.status.value,
            "emotional_resonance_count": self.emotional_resonance_count,
            "human_affection_score": self.human_affection_score,
            "ai_recognition_score": self.ai_recognition_score,
            "first_memory_time": self.first_memory_time.isoformat()
            if self.first_memory_time
            else None,
            "shared_tag_count": self.shared_tag_count,
            "last_relationship_stage": self.last_relationship_stage,
            "is_soulmate_link": self.is_soulmate_link,
            "manual_disconnection": self.manual_disconnection,
            "ai_sleep_triggered": self.ai_sleep_triggered,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Relationship":
        """
        Create a Relationship object from a dictionary.

        Args:
            data (dict): Dictionary containing Relationship data.

        Returns:
            Relationship: A Relationship object.
        """
        return cls(**data)