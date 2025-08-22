from fastapi import HTTPException, status, Depends
from typing import List
from ..models import (
    SaveMessageRequest, 
    UpdateWebResponseRequest, 
    GetMessagesResponse,
    ChatMessage
)
from ..auth.utils import (
    save_chat_message,
    update_chat_message_web_response,
    get_user_chat_messages,
    get_chat_message_by_id,
    delete_chat_message
)
from ..auth.deps import get_current_active_user
from ..auth.models import UserInDB

async def save_message(
    request: SaveMessageRequest,
    current_user: UserInDB = Depends(get_current_active_user)
) -> dict:
    """Save a new chat message with local response"""
    try:
        message_id = save_chat_message(
            user_id=current_user.username,
            message=request.message,
            local_response=request.local_response,
            local_citations=request.local_citations,
            metadata=request.metadata
        )
        
        return {
            "message_id": message_id,
            "status": "saved"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save message: {str(e)}"
        )

async def update_web_response(
    request: UpdateWebResponseRequest,
    current_user: UserInDB = Depends(get_current_active_user)
) -> dict:
    """Add web enrichment to existing message"""
    try:
        # Verify user owns the message
        message = get_chat_message_by_id(request.message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        if message["user_id"] != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this message"
            )
        
        success = update_chat_message_web_response(
            message_id=request.message_id,
            web_response=request.web_response,
            web_citations=request.web_citations
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update message"
            )
        
        return {
            "message_id": request.message_id,
            "status": "updated"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update message: {str(e)}"
        )

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