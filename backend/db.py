import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///' + (ROOT / 'data' / 'visionassist.db').as_posix())
(ROOT / 'data').mkdir(exist_ok=True)

class Base(DeclarativeBase):
    pass

def make_engine(url):
    engine = create_engine(url, connect_args={'check_same_thread': False} if url.startswith('sqlite') else {})
    if url.startswith('sqlite'):
        @event.listens_for(engine, 'connect')
        def configure_sqlite(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('PRAGMA busy_timeout=5000')
    return engine

engine = make_engine(DATABASE_URL)
SessionLocal = sessionmaker(engine, expire_on_commit=False)

def get_db():
    with SessionLocal() as db:
        yield db
