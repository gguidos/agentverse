from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class MongoDBClient:
    def __init__(self, db_uri: str, db_name: str):
        """
        Initialize the MongoDB client.

        Args:
            db_uri (str): MongoDB URI.
            db_name (str): Database name.
            db_collection_name (str): Collection name.
        """
        self.client = AsyncIOMotorClient(db_uri)
        self.db = self.client[db_name]
        self.db_uri = db_uri
        self.db_name = db_name
        self.collection = None

    async def connect(self) -> None:
        """Establish a connection to the MongoDB server."""
        try:
            if not self.client:
                # Create a new MongoDB client and connect to the database
                self.client = AsyncIOMotorClient(self.db_uri)
                self.db = self.client[self.db_name]
                logger.info(f"Connected to database '{self.db_name}' at '{self.db_uri}'")
            else:
                logger.info("MongoDB client already connected.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise


    async def disconnect(self) -> None:
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB.")

    def get_collection(self):
        """
        Get the collection object.

        Returns:
            The MongoDB collection object.
        """
        if self.collection is None:
            logger.error("MongoDB collection is not initialized. Please call `connect()` first.")
            raise ValueError("Collection is not initialized. Please call `connect()` first.")
        return self.collection

    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Dynamically retrieve a collection object."""
        if not self.db:
            raise Exception("Database connection not established. Call 'connect()' first.")
        return self.db[collection_name]

    async def insert_one(self, document: Dict[str, Any], collection_name: str) -> Any:
        """Insert a single document into a specified collection."""
        collection = self.get_collection(collection_name)
        result = await collection.insert_one(document)
        return result.inserted_id

    async def find(self, query: Dict[str, Any], collection_name: str) -> List[Dict[str, Any]]:
        """Find documents in the specified collection that match the query."""
        collection = self.get_collection(collection_name)
        documents = await collection.find(query).to_list(length=None)
        return documents

    async def delete_one(self, query: Dict[str, Any], collection_name: str) -> int:
        """Delete a single document from the specified collection that matches the query."""
        collection = self.get_collection(collection_name)
        result = await collection.delete_one(query)
        return result.deleted_count
