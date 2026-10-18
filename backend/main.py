import os
from pathlib import Path
import secrets
import time
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.exc import IntegrityError
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .db import ROOT, get_db
from .models import User, LoginSession, Enquiry, AuditEvent, Product, Quotation
from .schemas import LoginInput, EnquiryInput, AssignmentInput, QuoteInput
from .security import digest, hash_password, check_password, RateLimiter

app = FastAPI(title='VisionAssist', version='0.1.0', docs_url='/api/docs', redoc_url=None,
              openapi_url='/api/openapi.json')
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost', '127.0.0.1', 'testserver'])
limiter = RateLimiter()
ALLOWED_ORIGINS = {'http://localhost:8000', 'http://127.0.0.1:8000',
                   'http://localhost:5173', 'http://127.0.0.1:5173'}
DUMMY_PASSWORD = hash_password(secrets.token_urlsafe(32))

@app.middleware('http')
async def security_headers(request: Request, call_next):
    if request.url.path.startswith('/api/') and request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        if request.headers.get('X-VisionAssist') != '1':
            return JSONResponse({'detail': 'Missing request protection header'}, 403)
        origin = request.headers.get('origin')
        if origin and origin not in ALLOWED_ORIGINS:
            return JSONResponse({'detail': 'Origin not allowed'}, 403)
        try:
            length = int(request.headers.get('content-length', '0'))
        except ValueError:
            return JSONResponse({'detail': 'Invalid body length'}, 400)
        if length > 32768:
            return JSONResponse({'detail': 'Request too large'}, 413)
        body = await request.body()
        if len(body) > 32768:
            return JSONResponse({'detail': 'Request too large'}, 413)
    response = await call_next(request)
    response.headers.update({'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
                             'X-Frame-Options': 'DENY', 'Cache-Control': 'no-store'})
    if not request.url.path.startswith('/api/docs'):
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    return response

def limited(request, group, count, seconds=60):
    limiter.check((group, request.client.host if request.client else 'unknown'), count, seconds)

def current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get('va_session')
    session = db.get(LoginSession, digest(token)) if token else None
    if session is None or session.expires_at <= int(time.time()):
        raise HTTPException(401, 'Please sign in')
    return db.get(User, session.user_id)

def user_json(user):
    return {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role,
            'referral_code': user.referral_code}

def audit(db, enquiry, actor, action, details):
    db.add(AuditEvent(enquiry_id=enquiry.id, actor_id=actor.id if actor else None,
                      action=action, details=details))

def commit(db):
    try:
        db.commit()
    except (StaleDataError, IntegrityError):
        db.rollback()
        raise HTTPException(409, 'This record changed. Refresh and try again.')

def owned(db, enquiry_id, user):
    enquiry = db.get(Enquiry, enquiry_id)
    if not enquiry or (user.role != 'manager' and enquiry.assignee_id != user.id):
        raise HTTPException(404, 'Enquiry not found')
    return enquiry

def enquiry_json(e, db):
    assignee = db.get(User, e.assignee_id) if e.assignee_id else None
    referrer = db.get(User, e.original_referrer_id) if e.original_referrer_id else None
    return {'id': e.id, 'name': e.name, 'contact': e.contact, 'property_type': e.property_type,
            'location': e.location, 'requirements': e.requirements, 'status': e.status,
            'assignee_id': e.assignee_id, 'assignee_name': assignee.name if assignee else None,
            'original_referrer_id': e.original_referrer_id,
            'original_referrer_name': referrer.name if referrer else None,
            'revision': e.revision, 'created_at': e.created_at}

def quote_json(q):
    return {key: getattr(q, key) for key in ['id', 'version', 'created_at', 'status', 'items', 'total_paise', 'notes', 'price_kind']}

@app.get('/api/health')
def health():
    return {'status': 'ok', 'milestone': 1, 'mode': 'local prototype'}

@app.post('/api/auth/login')
def login(data: LoginInput, request: Request, response: Response, db: Session = Depends(get_db)):
    limited(request, 'login', 10, 300)
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    valid = check_password(data.password, user.password_hash if user else DUMMY_PASSWORD)
    if not user or not valid:
        raise HTTPException(401, 'Email or password is incorrect')
    token = secrets.token_urlsafe(32)
    old = request.cookies.get('va_session')
    if old:
        db.execute(delete(LoginSession).where(LoginSession.token_hash == digest(old)))
    db.execute(delete(LoginSession).where(LoginSession.expires_at <= int(time.time())))
    db.add(LoginSession(token_hash=digest(token), user_id=user.id, expires_at=int(time.time()) + 28800))
    db.commit()
    response.set_cookie('va_session', token, httponly=True, samesite='strict', max_age=28800,
                        secure=os.getenv('COOKIE_SECURE') == '1', path='/')
    return user_json(user)

@app.post('/api/auth/logout', status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get('va_session')
    if token:
        db.execute(delete(LoginSession).where(LoginSession.token_hash == digest(token)))
        db.commit()
    response.delete_cookie('va_session', path='/')

@app.get('/api/auth/me')
def me(user: User = Depends(current_user)):
    return user_json(user)

@app.get('/api/public/referral/{code}')
def referral(code: str, request: Request, db: Session = Depends(get_db)):
    limited(request, 'referral', 60)
    user = db.scalar(select(User).where(User.referral_code == code, User.role == 'salesperson'))
    if not user:
        raise HTTPException(404, 'Referral link is not valid')
    return {'name': user.name}

@app.post('/api/public/enquiries', status_code=201)
def create_enquiry(data: EnquiryInput, request: Request, db: Session = Depends(get_db)):
    limited(request, 'enquiry', 10, 3600)
    referrer = None
    if data.referral_code:
        referrer = db.scalar(select(User).where(User.referral_code == data.referral_code, User.role == 'salesperson'))
        if not referrer:
            raise HTTPException(400, 'Referral link is invalid. Open the general enquiry page to continue.')
    token = secrets.token_urlsafe(32)
    e = Enquiry(**data.model_dump(exclude={'referral_code', 'consent'}),
                original_referrer_id=referrer.id if referrer else None,
                assignee_id=referrer.id if referrer else None,
                status='assigned' if referrer else 'new', tracking_hash=digest(token),
                tracking_expires_at=int(time.time()) + 30 * 86400)
    db.add(e)
    db.flush()
    audit(db, e, None, 'enquiry_created', {'source': 'referral' if referrer else 'general',
                                         'assigned_to': e.assignee_id, 'contact_consent': True})
    db.commit()
    return {'id': e.id, 'tracking_token': token, 'expires_at': e.tracking_expires_at}

@app.get('/api/public/tracking')
def tracking(request: Request, db: Session = Depends(get_db)):
    limited(request, 'tracking', 60)
    token = request.headers.get('X-Tracking-Token', '')
    e = db.scalar(select(Enquiry).where(Enquiry.tracking_hash == digest(token))) if 20 <= len(token) <= 100 else None
    if not e or e.tracking_expires_at <= int(time.time()):
        raise HTTPException(404, 'Tracking link is invalid or expired')
    assignee = db.get(User, e.assignee_id) if e.assignee_id else None
    # Deliberately exclude contact, private requirements, assignment history and drafts.
    return {'id': e.id, 'status': 'in_review' if e.status == 'drafting' else e.status,
            'property_type': e.property_type, 'created_at': e.created_at,
            'salesperson': assignee.name if assignee else None,
            'message': 'Your enquiry is with our team. Quotation drafts remain private until reviewed and shared.'}

@app.get('/api/team')
def team(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != 'manager':
        raise HTTPException(403, 'Manager access required')
    return [user_json(u) for u in db.scalars(select(User).where(User.role == 'salesperson').order_by(User.name))]

@app.get('/api/enquiries')
def enquiries(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Enquiry).order_by(Enquiry.created_at.desc()).limit(200)
    if user.role != 'manager':
        query = query.where(Enquiry.assignee_id == user.id)
    return [enquiry_json(e, db) for e in db.scalars(query)]

@app.get('/api/enquiries/{enquiry_id}')
def enquiry_detail(enquiry_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    e = owned(db, enquiry_id, user)
    result = enquiry_json(e, db)
    result['history'] = [{'id': a.id, 'action': a.action, 'details': a.details, 'created_at': a.created_at,
                          'actor': db.get(User, a.actor_id).name if a.actor_id else 'Customer'}
                         for a in db.scalars(select(AuditEvent).where(AuditEvent.enquiry_id == e.id).order_by(AuditEvent.created_at))]
    result['quotations'] = [quote_json(q) for q in db.scalars(select(Quotation).where(Quotation.enquiry_id == e.id).order_by(Quotation.version.desc()))]
    return result

@app.post('/api/enquiries/{enquiry_id}/assignment')
def assign(enquiry_id: str, data: AssignmentInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != 'manager':
        raise HTTPException(403, 'Manager access required')
    e = owned(db, enquiry_id, user)
    if data.revision != e.revision:
        raise HTTPException(409, 'This enquiry changed. Refresh before assigning.')
    target = db.get(User, data.assignee_id) if data.assignee_id else None
    if data.assignee_id and (not target or target.role != 'salesperson'):
        raise HTTPException(400, 'Choose a salesperson')
    if e.assignee_id == data.assignee_id:
        raise HTTPException(400, 'Choose a different assignee')
    previous = db.get(User, e.assignee_id) if e.assignee_id else None
    audit(db, e, user, 'assignment_changed', {'from': e.assignee_id, 'to': data.assignee_id,
          'from_name': previous.name if previous else 'Unassigned', 'to_name': target.name if target else 'Unassigned', 'reason': data.reason})
    e.assignee_id = data.assignee_id
    e.status = 'assigned' if target else 'new'
    commit(db)
    return enquiry_json(e, db)

@app.get('/api/catalogue')
def catalogue(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [{key: getattr(p, key) for key in ['id', 'model', 'title', 'specs', 'evidence', 'verified', 'price_paise', 'price_kind']}
            for p in db.scalars(select(Product).where(Product.verified.is_(True)).order_by(Product.model))]

@app.get('/api/catalogue/{product_id}/source')
def source(product_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, 'Product not found')
    folder = (ROOT / 'data' / 'datasheets').resolve()
    path = (folder / p.evidence['filename']).resolve()
    if path.parent != folder or not path.is_file():
        raise HTTPException(404, 'Source PDF unavailable. Run the archive import first.')
    return FileResponse(path, media_type='application/pdf', filename=path.name, content_disposition_type='inline')

@app.post('/api/enquiries/{enquiry_id}/quotations', status_code=201)
def draft_quote(enquiry_id: str, data: QuoteInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    e = owned(db, enquiry_id, user)
    if user.role != 'salesperson' or e.assignee_id != user.id:
        raise HTTPException(403, 'Only the assigned salesperson can create a draft')
    if data.revision != e.revision:
        raise HTTPException(409, 'This enquiry changed. Refresh before drafting.')
    keys = [(line.product_id, line.lens) for line in data.items]
    if len(keys) != len(set(keys)):
        raise HTTPException(400, 'Combine duplicate model and lens selections')
    items = []
    for line in data.items:
        p = db.get(Product, line.product_id)
        if not p or not p.verified or line.lens not in p.specs.get('lens_options', []):
            raise HTTPException(400, 'Select a verified product and supported lens')
        items.append({'product_id': p.id, 'model': p.model, 'title': p.title, 'specs': p.specs,
                      'evidence': p.evidence, 'lens': line.lens, 'quantity': line.quantity,
                      'unit_price_paise': p.price_paise, 'line_total_paise': p.price_paise * line.quantity,
                      'price_kind': p.price_kind})
    version = (db.scalar(select(func.max(Quotation.version)).where(Quotation.enquiry_id == e.id)) or 0) + 1
    q = Quotation(enquiry_id=e.id, version=version, created_by=user.id, items=items,
                  total_paise=sum(x['line_total_paise'] for x in items), notes=data.notes,
                  price_kind='demo' if any(x['price_kind'] == 'demo' for x in items) else 'maintained')
    db.add(q)
    # An optimistic version update also serializes assignment-vs-quotation races.
    e.status = 'drafting'
    e.revision += 1
    audit(db, e, user, 'quotation_drafted', {'version': version, 'price_kind': q.price_kind})
    commit(db)
    return quote_json(q)

DIST = ROOT / 'frontend' / 'dist'
if DIST.exists():
    app.mount('/assets', StaticFiles(directory=DIST / 'assets'), name='assets')

    @app.get('/{path:path}', include_in_schema=False)
    def frontend(path: str):
        if path.startswith('api/'):
            raise HTTPException(404, 'Endpoint not found')
        return FileResponse(DIST / 'index.html')
