"""Database base configuration and session management."""
import os
import logging
from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# Create declarative base
Base = declarative_base()

# Global engine and session factory
_engine = None
_SessionFactory = None


def get_database_url() -> str:
    """Get database URL from environment."""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/safety_research_db"
    )
    return database_url


def get_engine(echo: bool = None) -> Engine:
    """
    Get or create SQLAlchemy engine with connection pooling.

    Args:
        echo: Whether to echo SQL queries (None = use env var)

    Returns:
        SQLAlchemy Engine instance
    """
    global _engine

    if _engine is None:
        database_url = get_database_url()

        if echo is None:
            echo = os.getenv("DB_ECHO", "False").lower() == "true"

        pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))

        _engine = create_engine(
            database_url,
            echo=echo,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_pre_ping=True,  # Verify connections before using
        )

        # Set up connection event listeners
        @event.listens_for(_engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Log new connections."""
            logger.debug("Database connection established")

        @event.listens_for(_engine, "close")
        def receive_close(dbapi_conn, connection_record):
            """Log connection closures."""
            logger.debug("Database connection closed")

        logger.info(
            f"Database engine created (pool_size={pool_size}, "
            f"max_overflow={max_overflow})"
        )

    return _engine


def get_session_factory() -> sessionmaker:
    """Get or create session factory."""
    global _SessionFactory

    if _SessionFactory is None:
        engine = get_engine()
        _SessionFactory = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
        logger.info("Database session factory created")

    return _SessionFactory


def get_session() -> Session:
    """
    Get a new database session.

    Returns:
        SQLAlchemy Session instance

    Note:
        Caller is responsible for closing the session.
    """
    SessionFactory = get_session_factory()
    return SessionFactory()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with automatic cleanup.

    Yields:
        SQLAlchemy Session instance

    Example:
        >>> with get_db_context() as session:
        ...     case = session.query(CaseDB).first()
        ...     print(case.title)
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def init_db(drop_all: bool = False) -> None:
    """
    Initialize database schema.

    Args:
        drop_all: If True, drop all tables before creating (USE WITH CAUTION!)

    Warning:
        Setting drop_all=True will DELETE ALL DATA in the database!
    """
    engine = get_engine()

    if drop_all:
        logger.warning("Dropping all database tables")
        Base.metadata.drop_all(bind=engine)

    logger.info("Creating database tables")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialization complete")


def close_db() -> None:
    """Close database engine and cleanup resources."""
    global _engine, _SessionFactory

    if _engine:
        _engine.dispose()
        _engine = None
        logger.info("Database engine disposed")

    _SessionFactory = None
