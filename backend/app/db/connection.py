import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

logger = logging.getLogger("interviewiq.db")

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo() -> Optional[AsyncIOMotorDatabase]:
    """
    Establishes async connection to MongoDB via Motor using MONGODB_URI and MONGODB_DB_NAME.
    If MongoDB is unreachable, logs a warning and returns None to allow graceful fallback.
    """
    global _client, _db
    try:
        uri = settings.MONGODB_URI or "mongodb://localhost:27017"
        db_name = settings.MONGODB_DB_NAME or "interviewiq_db"
        logger.info(f"Connecting to MongoDB at {uri} (database: {db_name})...")
        
        _client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=2000)
        # Ping the server to verify connectivity
        await _client.admin.command("ping")
        _db = _client[db_name]
        logger.info("Successfully connected to MongoDB.")
        return _db
    except Exception as exc:
        logger.warning(
            f"Could not establish connection to MongoDB ({type(exc).__name__}: {exc}). "
            "Application will use in-memory repository storage for development/testing."
        )
        _db = None
        return None


async def close_mongo_connection():
    """Closes the MongoDB Motor client connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("Closed MongoDB connection.")


def get_db() -> Optional[AsyncIOMotorDatabase]:
    """Returns active database handle if connected, else None."""
    return _db
