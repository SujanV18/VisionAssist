"""Explicit, idempotent demo data. Never runs at application startup."""
import hashlib
import json
import secrets
import time
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from .db import ROOT, SessionLocal
from .models import User, Product, Enquiry, AuditEvent
from .security import hash_password, digest

DEMO_PASSWORD = 'VisionDemo!2026'

def seed(db):
    people = {}
    for email, name, role, code in [
        ('manager@visionassist.demo', 'Meera Shah', 'manager', None),
        ('arjun@visionassist.demo', 'Arjun Rao', 'salesperson', 'arjun-demo'),
        ('priya@visionassist.demo', 'Priya Nair', 'salesperson', 'priya-demo')]:
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(email=email, name=name, role=role, referral_code=code, password_hash=hash_password(DEMO_PASSWORD))
            db.add(user)
            db.flush()
        people[email.split('@')[0]] = user
    catalogue = json.loads((ROOT / 'data' / 'verified_catalogue.json').read_text(encoding='utf-8'))
    for row in catalogue:
        source = ROOT / 'data' / 'datasheets' / row['evidence']['filename']
        if source.exists() and hashlib.sha256(source.read_bytes()).hexdigest() != row['evidence']['sha256']:
            raise ValueError(f'Source hash mismatch for {row["model"]}')
        if not db.scalar(select(Product).where(Product.model == row['model'])):
            db.add(Product(**row))
    for index, (name, property_type, location, note, owner, referrer) in enumerate([
        ('Demo · Lotus Mart', 'Shop', 'Bengaluru · Jayanagar', 'Four camera positions covering the entrance, checkout and two aisles. Please review blind spots.', None, None),
        ('Demo · Northstar Storage', 'Warehouse', 'Bengaluru · Peenya', 'Six proposed camera positions around loading bays and indoor stock aisles. Lighting and cable runs need a site survey.', 'arjun', 'arjun'),
        ('Demo · Greenview Home', 'Home', 'Bengaluru · Whitefield', 'Two camera positions for the gate and driveway. Would like help choosing lens coverage.', 'priya', None),
        ('Demo · Studio Eight', 'Office', 'Bengaluru · Indiranagar', 'Three camera positions for reception and common areas. Discuss staff privacy before final placement.', None, None),
    ]):
        if db.scalar(select(Enquiry).where(Enquiry.name == name)):
            continue
        e = Enquiry(name=name, property_type=property_type, location=location, requirements=note,
                    contact=f'fixture{index+1}@example.invalid', assignee_id=people[owner].id if owner else None,
                    original_referrer_id=people[referrer].id if referrer else None,
                    status='assigned' if owner else 'new', tracking_hash=digest(secrets.token_urlsafe(32)),
                    tracking_expires_at=int(time.time()) + 30 * 86400,
                    created_at=(datetime.now(timezone.utc) - timedelta(hours=index * 3 + 1)).isoformat())
        db.add(e)
        db.flush()
        db.add(AuditEvent(enquiry_id=e.id, actor_id=None, action='demo_fixture_created',
                          details={'source': 'referral' if referrer else 'general', 'synthetic': True}))
    db.commit()

if __name__ == '__main__':
    with SessionLocal() as db:
        seed(db)
    print('Local demo ready: manager / arjun / priya @visionassist.demo')
    print('Demo password: ' + DEMO_PASSWORD)
