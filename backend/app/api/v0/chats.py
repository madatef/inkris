from uuid import UUID

from fastapi import APIRouter, Depends, Path, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_conversation, get_db, get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    UserConversationsRequest,
    UserConversationsResponse,
    ConversationMessages,
    ConversationMessagesResponse,
    ChatMessageCreate,
)
from app.services.chats import (
    create_conversation,
    delete_conversation,
    agent_streamer,
    get_user_conversations,
    get_conversation_messages,
    update_conversation_title,
)


router = APIRouter(prefix="/chat", tags=["chat", "conversation", "messages"])


@router.post("/conversations/create", response_model=ConversationResponse)
async def create(
    data: ConversationCreate,
    response: Response,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):

    conv = await create_conversation(
        session,
        user_id=user.id,
        data=data,
    )
    await session.commit()
    response.status_code = status.HTTP_201_CREATED
    return conv

@router.patch("/conversations/{id}/rename", response_model=ConversationResponse)
async def patch_convo(
    data: ConversationUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    id: UUID = Path(...),
):
    updated = await update_conversation_title(session, user_id=user.id, conv_id=id, title=data.title)
    await session.commit()
    return updated

@router.delete("/conversations/{id}")
async def delete(
    response: Response,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    id = Path(...),
):
    await delete_conversation(session, id=id, user_id=user.id)
    await session.commit()
    response.status_code = status.HTTP_204_NO_CONTENT
    return

# Use POST to allow request body on all browsers/proxies. Request body provides better and easier validation than query params.
@router.post("/conversations/all", response_model=UserConversationsResponse)
async def user_conversations(
    data: UserConversationsRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await get_user_conversations(session, user_id=user.id, page=data.page, page_size=data.page_size)
    return result

@router.post("/conversations/{id}/list-messages", response_model=ConversationMessagesResponse)
async def get_messages(
    data: ConversationMessages,
    session: AsyncSession = Depends(get_db),
    conv: Conversation = Depends(get_current_conversation),
):
    return await get_conversation_messages(
        session,
        user_id=conv.user_id,
        conversation_id=conv.id,
        limit=data.limit,
        cursor=data.cursor,
    )

@router.post("/conversations/{id}/messages")
async def send_message(
    data: ChatMessageCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    conv: Conversation = Depends(get_current_conversation),
):

    return StreamingResponse(
        agent_streamer(session, msg=data.content, user_name=f"{user.last_name}, {user.first_name}", conv=conv), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disables nginx buffering for production
        },
    )
