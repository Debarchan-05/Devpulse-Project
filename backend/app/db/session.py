from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


# pool_recycle=280 matters for MySQL specifically: MySQL closes idle
# connections after `wait_timeout` seconds (default 28800s on most
# installs, but far less on some managed/free-tier hosts). Recycling
# pooled connections just under that window avoids the classic
# "MySQL server has gone away" error on an app that's been idle for a
# while. pool_pre_ping adds a lightweight SELECT 1 check before handing
# a connection out, so a dropped connection is replaced instead of
# raising an error on your request.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=280,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
