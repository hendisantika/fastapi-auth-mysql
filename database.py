import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:password@localhost:3306/fastapi_auth",
)

# Asia/Jakarta (WIB) is UTC+7 year-round (no DST). Setting the session time zone
# ensures MySQL NOW()/CURRENT_TIMESTAMP defaults (created_at/updated_at) are WIB.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"init_command": "SET time_zone = '+07:00'"},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
