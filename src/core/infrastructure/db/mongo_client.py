from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class MongoDBClient:
    def __init__(self, db_uri: str, db_name: str, db_collection: str):
        """
        Initialize the MongoDB client.

        Args:
            db_uri (str): MongoDB URI.
            db_name (str): Database name.
            db_collection_name (str): Collection name.
        """
        self.db_uri = db_uri
        self.db_name = db_name
        self.db_collection_name = db_collection
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.collection = None

    async def connect(self) -> None:
        """Establish a connection to the MongoDB server."""
        try:
            if not self.client:
                # Create a new MongoDB client and connect to the database and collection
                self.client = AsyncIOMotorClient(self.db_uri)
                self.db = self.client[self.db_name]
                self.collection = self.db[self.db_collection_name]  # Set the collection object
                logger.info(f"Connected to database '{self.db_name}' at '{self.db_uri}' with collection '{self.db_collection_name}'")
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

    async def insert_one(self, document: Dict[str, Any]) -> Any:
        """Insert a single document into the collection."""
        collection = self.get_collection()
        result = await collection.insert_one(document)
        return result.inserted_id

    async def find(self, query: Dict[str, Any]) -> list:
        """Find documents in the collection that match the query."""
        collection = self.get_collection()
        documents = await collection.find(query).to_list(length=None)
        return documents

    async def delete_one(self, query: Dict[str, Any]) -> int:
        """Delete a single document from the collection that matches the query."""
        collection = self.get_collection()
        result = await collection.delete_one(query)
        return result.deleted_count
