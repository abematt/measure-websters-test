from fastapi import HTTPException, status, Depends
from typing import List
from ..models import (
    GetMessagesResponse,
    ChatMessage
)
from ..auth.utils import (
    get_user_chat_messages,
    get_chat_message_by_id,
    delete_chat_message
)
from ..auth.deps import get_current_active_user
from ..auth.models import UserInDB

async def get_messages(
    limit: int = 50,
    offset: int = 0,
    current_user: UserInDB = Depends(get_current_active_user)
) -> GetMessagesResponse:
    """Get user's chat message history"""
    try:
        messages_data = get_user_chat_messages(
            user_id=current_user.username,
            limit=limit,
            offset=offset
        )
        
        messages = [ChatMessage(**msg) for msg in messages_data]
        
        return GetMessagesResponse(
            messages=messages,
            total=len(messages)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get messages: {str(e)}"
        )

async def delete_message(
    message_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
) -> dict:
    """Delete a chat message"""
    try:
        success = delete_chat_message(
            message_id=message_id,
            user_id=current_user.username
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or not authorized"
            )
        
        return {
            "message_id": message_id,
            "status": "deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete message: {str(e)}"
        )