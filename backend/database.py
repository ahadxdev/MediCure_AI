from typing import Generator
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.config import settings

# Configure engine with connection pooling and dialect options
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Creates database tables if they do not exist."""
    # Import all models to ensure they are registered with Base.metadata
    from backend.models import entities  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Add quote inbox metadata to databases created before Gmail sync existed.
    quote_columns = {
        "supplier_name": "VARCHAR(255)",
        "medicine_name": "VARCHAR(255)",
        "source_message_id": "VARCHAR(255)",
        "source_thread_id": "VARCHAR(255)",
        "source_email": "VARCHAR(255)",
    }
    existing_columns = {
        column["name"] for column in inspect(engine).get_columns("quotations")
    }
    with engine.begin() as connection:
        for name, sql_type in quote_columns.items():
            if name not in existing_columns:
                connection.exec_driver_sql(
                    f"ALTER TABLE quotations ADD COLUMN {name} {sql_type}"
                )

    for index in entities.Quotation.__table__.indexes:
        index.create(bind=engine, checkfirst=True)
