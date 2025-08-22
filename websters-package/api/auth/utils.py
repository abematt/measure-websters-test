import os
from datetime import datetime, timedelta
from typing import Optional, Union, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from pymongo.database import Database
from bson import ObjectId
from .models import User, UserInDB, TokenData
from ..database.connection import get_database

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return TokenData(username=username)
    except JWTError:
        return None

def get_user_by_username(username: str) -> Optional[UserInDB]:
    """Get user from database by username"""
    db = get_database()
    user_data = db.users.find_one({"username": username})
    if user_data:
        # Convert MongoDB _id to string
        user_data["_id"] = str(user_data["_id"])
        return UserInDB(**user_data)
    return None

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user with username and password"""
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user

def update_last_login(username: str):
    """Update user's last login timestamp"""
    db = get_database()
    db.users.update_one(
        {"username": username},
        {"$set": {"last_login": datetime.utcnow()}}
    )

# Chat message CRUD operations
def save_chat_message(user_id: str, message: str, local_response: str, 
                     local_citations: List[dict], metadata: Optional[dict] = None) -> str:
    """Save a new chat message with local response"""
    db = get_database()
    
    chat_doc = {
        "user_id": user_id,
        "message": message,
        "local_response": local_response,
        "local_citations": local_citations,
        "web_response": None,
        "web_citations": [],
        "is_web_enriched": False,
        "timestamp": datetime.utcnow(),
        "updated_at": None,
        "metadata": metadata
    }
    
    result = db.chat_messages.insert_one(chat_doc)
    return str(result.inserted_id)

def update_chat_message_web_response(message_id: str, web_response: str, 
                                   web_citations: List[dict]) -> bool:
    """Update existing message with web enrichment"""
    db = get_database()
    
    result = db.chat_messages.update_one(
        {"_id": ObjectId(message_id)},
        {
            "$set": {
                "web_response": web_response,
                "web_citations": web_citations,
                "is_web_enriched": True,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return result.modified_count > 0

def get_user_chat_messages(user_id: str, limit: int = 50, offset: int = 0) -> List[dict]:
    """Get chat messages for a user"""
    db = get_database()
    
    cursor = db.chat_messages.find({"user_id": user_id}) \
        .sort("timestamp", -1) \
        .skip(offset) \
        .limit(limit)
    
    messages = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        messages.append(doc)
    
    return messages

def get_chat_message_by_id(message_id: str) -> Optional[dict]:
    """Get a specific chat message by ID"""
    db = get_database()
    
    doc = db.chat_messages.find_one({"_id": ObjectId(message_id)})
    if doc:
        doc["_id"] = str(doc["_id"])
        return doc
    return None

def delete_chat_message(message_id: str, user_id: str) -> bool:
    """Delete a chat message (only by owner)"""
    db = get_database()
    
    result = db.chat_messages.delete_one({
        "_id": ObjectId(message_id),
        "user_id": user_id
    })
    
    return result.deleted_count > 0