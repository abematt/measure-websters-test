import os
from pymongo import MongoClient
from pymongo.database import Database
from typing import Optional

class DatabaseConnection:
    """MongoDB connection manager"""
    
    _instance: Optional['DatabaseConnection'] = None
    _client: Optional[MongoClient] = None
    _database: Optional[Database] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def connect(self) -> Database:
        """Connect to MongoDB and return database instance"""
        if self._database is None:
            mongodb_url = os.getenv("MONGODB_URL")
            print("Connecting to",mongodb_url)
            database_name = os.getenv("DATABASE_NAME", "websters_auth")
            
            self._client = MongoClient(mongodb_url)
            self._database = self._client[database_name]
            
            # Test connection
            self._client.admin.command('ping')
            print(f"Connected to MongoDB: {database_name}")
            
        return self._database
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            print("Disconnected from MongoDB")

# Global database instance
db_connection = DatabaseConnection()

def get_database() -> Database:
    """Get database instance"""
    return db_connection.connect()