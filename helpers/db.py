"""Database helper module for MongoDB connections."""

import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = os.getenv("MONGODB_URI")


def get_database(db_name: str):
    """Get a MongoDB database instance."""
    client = AsyncIOMotorClient(MONGODB_URI)
    return client[db_name]
