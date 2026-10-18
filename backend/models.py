from datetime import datetime, timezone
import uuid
from sqlalchemy import String, Integer, Text, ForeignKey, JSON, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def uid():
    return str(uuid.uuid4())

def now():
    return datetime.now(timezone.utc).isoformat()

class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(20))
    referral_code: Mapped[str | None] = mapped_column(String(64), unique=True)
    __table_args__ = (CheckConstraint("role IN ('manager', 'salesperson')", name='valid_role'),)

class LoginSession(Base):
    __tablename__ = 'sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    expires_at: Mapped[int] = mapped_column(Integer)

class Enquiry(Base):
    __tablename__ = 'enquiries'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(100))
    contact: Mapped[str] = mapped_column(String(254))
    property_type: Mapped[str] = mapped_column(String(30))
    location: Mapped[str] = mapped_column(String(200))
    requirements: Mapped[str] = mapped_column(Text)
    original_referrer_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    assignee_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), index=True)
    status: Mapped[str] = mapped_column(String(30), default='new')
    revision: Mapped[int] = mapped_column(Integer, default=1)
    tracking_hash: Mapped[str] = mapped_column(String(64), unique=True)
    tracking_expires_at: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(String(40), default=now)
    __mapper_args__ = {'version_id_col': revision}

class AuditEvent(Base):
    __tablename__ = 'audit_events'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    enquiry_id: Mapped[str] = mapped_column(ForeignKey('enquiries.id'), index=True)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    action: Mapped[str] = mapped_column(String(60))
    details: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(String(40), default=now)

class Product(Base):
    __tablename__ = 'products'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    model: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    specs: Mapped[dict] = mapped_column(JSON)
    evidence: Mapped[dict] = mapped_column(JSON)
    verified: Mapped[bool] = mapped_column(default=False)
    price_paise: Mapped[int] = mapped_column(Integer)
    price_kind: Mapped[str] = mapped_column(String(20), default='demo')
    __table_args__ = (CheckConstraint('price_paise > 0', name='positive_price'),)

class Quotation(Base):
    __tablename__ = 'quotations'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    enquiry_id: Mapped[str] = mapped_column(ForeignKey('enquiries.id'), index=True)
    version: Mapped[int] = mapped_column(Integer)
    created_by: Mapped[str] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[str] = mapped_column(String(40), default=now)
    status: Mapped[str] = mapped_column(String(20), default='draft')
    items: Mapped[list] = mapped_column(JSON)
    total_paise: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str] = mapped_column(Text)
    price_kind: Mapped[str] = mapped_column(String(20), default='demo')
    __table_args__ = (UniqueConstraint('enquiry_id', 'version', name='unique_quote_version'),)
