import truststore
truststore.inject_into_ssl()

"""
DB models: RoadmapTopic + PostedLog + RoadmapRun
--------------------------------------------------
RoadmapTopic  - a single learning roadmap item (Day N -> topic -> subtopic)
PostedLog     - the single source of truth for duplicate checks and post status
RoadmapRun    - represents one active (or stopped) roadmap campaign;
                only one row should have status == 'running' at any given time
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.sql import func
from app.db.database import Base


class RoadmapTopic(Base):
    """
    A single learning roadmap item, e.g. Day 12 -> 'Django ORM' -> 'QuerySet optimization'
    """
    __tablename__ = "roadmap_topics"

    id = Column(Integer, primary_key=True, index=True)
    day_or_order = Column(Integer, nullable=False)      # sequence in the roadmap
    topic = Column(String(255), nullable=False)
    subtopic = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)                 # optional learning notes to feed the Generator
    priority = Column(Integer, default=0)               # higher = pick sooner, if not sequential
    roadmap_run_id = Column(Integer, nullable=True, index=True)  # links this topic to a specific roadmap campaign


class PostedLog(Base):
    """
    Tracks every generated/posted item -> the single source of truth for duplicate checks.
    status: 'pending_approval' | 'posted' | 'rejected' | 'skipped' | 'auto_rejected' | 'publish_failed'
    """
    __tablename__ = "posted_log"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(255), nullable=False)
    subtopic = Column(String(255), nullable=True)
    content_text = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    embedding_json = Column(Text, nullable=True)   # store embedding vector as JSON for similarity checks
    status = Column(String(32), nullable=False, default="pending_approval")
    approval_token = Column(String(512), nullable=True)
    approval_deadline = Column(DateTime(timezone=True), nullable=True)
    linkedin_post_urn = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    posted_at = Column(DateTime(timezone=True), nullable=True)
    similarity_score = Column(Float, nullable=True)
    roadmap_run_id = Column(Integer, nullable=True, index=True)  # links this post to a specific roadmap campaign


class RoadmapRun(Base):
    """
    Represents one active (or stopped) roadmap campaign.
    Only one row should have status == 'running' at any given time.
    """
    __tablename__ = "roadmap_runs"

    id = Column(Integer, primary_key=True, index=True)
    roadmap_filename = Column(String(255), nullable=True)
    total_days = Column(Integer, nullable=False)
    status = Column(String(32), nullable=False, default="running")  # running | stopped
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    stopped_at = Column(DateTime(timezone=True), nullable=True)