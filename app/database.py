
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Store the database in the project root folder.
DATABASE_URL = "sqlite:///./certificates.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


def get_db():
    """Provide a database session and close it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
