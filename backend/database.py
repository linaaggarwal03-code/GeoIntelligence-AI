from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

# Normalize legacy postgres:// scheme to postgresql:// if needed
database_url = settings.DATABASE_URL
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Dialect-specific engine configurations
connect_args = {}
engine_kwargs = {"pool_pre_ping": True}

if database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    # PostgreSQL connection pool settings
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
    })

engine = create_engine(
    database_url,
    connect_args=connect_args,
    **engine_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a SQLAlchemy session per request
    and guarantees its closure upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
