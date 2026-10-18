import hashlib
import json
import time
import zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import StaleDataError
from backend.db import Base, make_engine, get_db, ROOT
from backend.models import Enquiry, Product, LoginSession, AuditEvent
from backend.main import app, limiter
from backend.seed import seed, DEMO_PASSWORD
from scripts.inspect_archive import inspect

@pytest.fixture
def env(tmp_path):
    engine = make_engine('sqlite:///' + (tmp_path / 'test.db').as_posix())
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as db:
        seed(db)
    def override():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = override
    limiter.buckets.clear()
    with TestClient(app, headers={'X-VisionAssist': '1'}) as client:
        yield client, factory
    app.dependency_overrides.clear()
    engine.dispose()

def login(client, who='manager'):
    response = client.post('/api/auth/login', json={'email': who+'@visionassist.demo', 'password': DEMO_PASSWORD})
    assert response.status_code == 200, response.text
    return response.json()

def submit(client, referral=None):
    response = client.post('/api/public/enquiries', json={'name':'Test Customer', 'contact':'customer@example.invalid',
        'property_type':'Shop', 'location':'Bengaluru', 'requirements':'Cover the entrance and checkout area.',
        'consent':True, 'referral_code':referral})
    assert response.status_code == 201, response.text
    return response.json()

def test_full_general_assignment_draft_flow(env):
    client, _ = env
    receipt = submit(client)
    manager = login(client)
    lead = client.get('/api/enquiries/'+receipt['id']).json()
    assert lead['assignee_id'] is None and lead['original_referrer_id'] is None
    team = client.get('/api/team').json()
    arjun = next(u for u in team if u['name']=='Arjun Rao')
    result = client.post(f'/api/enquiries/{lead["id"]}/assignment', json={'assignee_id':arjun['id'],'revision':lead['revision'],'reason':'Area coverage'})
    assert result.status_code == 200
    login(client, 'arjun')
    lead = client.get('/api/enquiries/'+lead['id']).json()
    product = client.get('/api/catalogue').json()[0]
    quote = client.post(f'/api/enquiries/{lead["id"]}/quotations', json={'revision':lead['revision'], 'items':[{'product_id':product['id'],'quantity':3,'lens':'2.8 mm'}],'notes':'Survey pending'})
    assert quote.status_code == 201, quote.text
    q = quote.json()
    assert q['total_paise']==3*product['price_paise'] and q['version']==1 and q['price_kind']=='demo'
    assert q['items'][0]['evidence']['sha256'] == product['evidence']['sha256']
    assert manager['role'] == 'manager'

def test_referral_reassignment_preserves_origin_and_revokes_old_access(env):
    client, _ = env
    receipt = submit(client, 'arjun-demo')
    arjun = login(client, 'arjun')
    lead = client.get('/api/enquiries/'+receipt['id']).json()
    assert lead['assignee_id']==arjun['id']==lead['original_referrer_id']
    login(client)
    priya = next(u for u in client.get('/api/team').json() if u['name']=='Priya Nair')
    changed = client.post(f'/api/enquiries/{lead["id"]}/assignment', json={'assignee_id':priya['id'],'revision':lead['revision'],'reason':'Territory change'}).json()
    assert changed['original_referrer_id']==arjun['id'] and changed['assignee_id']==priya['id']
    login(client, 'arjun')
    assert client.get('/api/enquiries/'+lead['id']).status_code==404
    assert lead['id'] not in [e['id'] for e in client.get('/api/enquiries').json()]
    login(client, 'priya')
    detail = client.get('/api/enquiries/'+lead['id']).json()
    assert detail['history'][-1]['details']['reason']=='Territory change'

def test_salesperson_cannot_assign_or_list_team_or_read_unowned(env):
    client, _ = env
    receipt = submit(client)
    login(client, 'arjun')
    assert client.get('/api/team').status_code==403
    assert client.get('/api/enquiries/'+receipt['id']).status_code==404
    assert client.post(f'/api/enquiries/{receipt["id"]}/assignment', json={'assignee_id':None,'revision':1,'reason':'Attempt'}).status_code==403

def test_tracking_is_scoped_and_excludes_private_fields(env):
    client, _ = env
    receipt = submit(client, 'arjun-demo')
    other = submit(client)
    response = client.get('/api/public/tracking',headers={'X-Tracking-Token':receipt['tracking_token']})
    assert response.status_code==200
    assert response.json()['id']==receipt['id']!=other['id']
    for private in ['contact','name','requirements','tracking_hash','quotations','history']:
        assert private not in response.json()
    assert client.get('/api/public/tracking',headers={'X-Tracking-Token':'invalid-token-does-not-exist'}).status_code==404

def test_tracking_expiry_and_hashed_tokens(env):
    client, factory = env
    receipt = submit(client)
    with factory() as db:
        e = db.get(Enquiry,receipt['id'])
        assert e.tracking_hash==hashlib.sha256(receipt['tracking_token'].encode()).hexdigest()
        e.tracking_expires_at=int(time.time())-1
        db.commit()
    assert client.get('/api/public/tracking',headers={'X-Tracking-Token':receipt['tracking_token']}).status_code==404

def test_session_logout_expiry_and_csrf(env):
    client, factory = env
    assert client.get('/api/enquiries').status_code==401
    login(client)
    assert 'HttpOnly' in client.post('/api/auth/login',json={'email':'manager@visionassist.demo','password':DEMO_PASSWORD}).headers['set-cookie']
    assert client.post('/api/auth/logout',headers={'Origin':'https://attacker.invalid'}).status_code==403
    assert client.post('/api/auth/logout',headers={'X-VisionAssist':''}).status_code==403
    with factory() as db:
        session=db.scalar(select(LoginSession))
        session.expires_at=int(time.time())-1
        db.commit()
    assert client.get('/api/enquiries').status_code==401
    login(client)
    assert client.post('/api/auth/logout').status_code==204
    assert client.get('/api/enquiries').status_code==401

def test_invalid_referral_and_contact_are_rejected(env):
    client, _ = env
    data={'name':'Alex','contact':'not-a-contact','property_type':'Home','location':'Bengaluru','requirements':'Entrance coverage','consent':True}
    assert client.post('/api/public/enquiries',json=data).status_code==422
    data.update(contact='alex@example.invalid',referral_code='missing')
    assert client.post('/api/public/enquiries',json=data).status_code==400
    data.update(referral_code=None,consent=False)
    assert client.post('/api/public/enquiries',json=data).status_code==422

def test_stale_assignment_and_manager_target_rejected(env):
    client, _ = env
    receipt=submit(client)
    manager=login(client)
    team=client.get('/api/team').json()
    url=f'/api/enquiries/{receipt["id"]}/assignment'
    assert client.post(url,json={'assignee_id':manager['id'],'revision':1,'reason':'Invalid role'}).status_code==400
    assert client.post(url,json={'assignee_id':team[0]['id'],'revision':1,'reason':'Assign first'}).status_code==200
    assert client.post(url,json={'assignee_id':team[1]['id'],'revision':1,'reason':'Stale write'}).status_code==409

def test_quote_versions_snapshot_and_drafts_hidden(env):
    client, factory = env
    receipt=submit(client,'arjun-demo')
    login(client,'arjun')
    product=client.get('/api/catalogue').json()[0]
    url=f'/api/enquiries/{receipt["id"]}/quotations'
    data={'revision':1,'items':[{'product_id':product['id'],'quantity':2,'lens':'4 mm'}]}
    first=client.post(url,json=data).json()
    assert client.post(url,json=data).status_code==409
    with factory() as db:
        p=db.get(Product,product['id']); p.price_paise+=10000; db.commit()
    data['revision']=client.get('/api/enquiries/'+receipt['id']).json()['revision']
    second=client.post(url,json=data).json()
    assert second['version']==2 and second['total_paise']==first['total_paise']+20000
    versions=client.get('/api/enquiries/'+receipt['id']).json()['quotations']
    assert versions[1]['total_paise']==first['total_paise']
    tracked=client.get('/api/public/tracking',headers={'X-Tracking-Token':receipt['tracking_token']}).json()
    assert tracked['status']=='in_review' and 'quotations' not in tracked

@pytest.mark.parametrize('change',[{'quantity':0},{'quantity':101},{'quantity':1.5},{'lens':'8 mm'},{'unit_price_paise':1}])
def test_invalid_quote_lines_cannot_override_server_values(env,change):
    client,_=env
    receipt=submit(client,'arjun-demo');login(client,'arjun')
    p=client.get('/api/catalogue').json()[0]
    line={'product_id':p['id'],'quantity':1,'lens':'2.8 mm',**change}
    assert client.post(f'/api/enquiries/{receipt["id"]}/quotations',json={'revision':1,'items':[line]}).status_code==422

def test_manager_cannot_draft_and_unverified_product_blocked(env):
    client,factory=env
    receipt=submit(client,'arjun-demo');login(client)
    p=client.get('/api/catalogue').json()[0]
    data={'revision':1,'items':[{'product_id':p['id'],'quantity':1,'lens':'2.8 mm'}]}
    url=f'/api/enquiries/{receipt["id"]}/quotations'
    assert client.post(url,json=data).status_code==403
    login(client,'arjun')
    with factory() as db:
        product=db.get(Product,p['id']);product.verified=False;db.commit()
    assert client.post(url,json=data).status_code==400

def test_duplicate_lines_and_empty_quote_rejected(env):
    client,_=env
    receipt=submit(client,'arjun-demo');login(client,'arjun')
    p=client.get('/api/catalogue').json()[0]
    line={'product_id':p['id'],'quantity':1,'lens':'2.8 mm'}
    url=f'/api/enquiries/{receipt["id"]}/quotations'
    assert client.post(url,json={'revision':1,'items':[line,line]}).status_code==400
    assert client.post(url,json={'revision':1,'items':[]}).status_code==422

def test_archive_traversal_rejected_before_writing(tmp_path):
    archive=tmp_path/'unsafe.zip';out=tmp_path/'out'
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr('../outside.pdf',b'%PDF-1.7')
    with pytest.raises(ValueError,match='Unsafe'):
        inspect(archive,out)
    assert not out.exists()

def test_catalogue_evidence_matches_inspected_archive():
    manifest=json.loads((ROOT/'data/archive_manifest.json').read_text())
    catalogue=json.loads((ROOT/'data/verified_catalogue.json').read_text())
    assert manifest['pdf_count']==66 and len(catalogue)==3
    files={f['filename']:f for f in manifest['files']}
    for product in catalogue:
        evidence=product['evidence']
        assert evidence['sha256']==files[evidence['filename']]['sha256']
        assert product['price_kind']=='demo'
        source=ROOT/'data/datasheets'/evidence['filename']
        if source.exists():
            assert hashlib.sha256(source.read_bytes()).hexdigest()==evidence['sha256']

def test_rate_limit_and_bad_login(env):
    client,_=env
    for _ in range(10):
        assert client.post('/api/auth/login',json={'email':'unknown@example.invalid','password':'bad'}).status_code==401
    assert client.post('/api/auth/login',json={'email':'unknown@example.invalid','password':'bad'}).status_code==429

def test_oversized_request_and_unknown_fields(env):
    client,_=env
    assert client.post('/api/public/enquiries',content='x'*33000).status_code==413
    assert client.post('/api/auth/login',json={'email':'manager@visionassist.demo','password':DEMO_PASSWORD,'role':'manager'}).status_code==422

def test_seed_idempotent(env):
    client,factory=env
    with factory() as db:
        seed(db)
    login(client)
    assert len(client.get('/api/enquiries').json())==4
    assert len(client.get('/api/catalogue').json())==3

def test_concurrent_sessions_cannot_silently_overwrite_ownership(env):
    client,factory=env
    receipt=submit(client,'arjun-demo')
    with factory() as first, factory() as second:
        a=first.get(Enquiry,receipt['id'])
        b=second.get(Enquiry,receipt['id'])
        a.assignee_id=None
        a.status='new'
        first.commit()
        b.status='drafting'
        with pytest.raises(StaleDataError):
            second.commit()

def test_pdf_source_requires_login(env):
    client,_=env
    login(client)
    product=client.get('/api/catalogue').json()[0]
    path='/api/catalogue/'+product['id']+'/source'
    response=client.get(path)
    source=ROOT/'data/datasheets'/product['evidence']['filename']
    if source.exists():
        assert response.status_code==200 and response.content.startswith(b'%PDF-')
    else:
        assert response.status_code==404
    client.post('/api/auth/logout')
    assert client.get(path).status_code==401
