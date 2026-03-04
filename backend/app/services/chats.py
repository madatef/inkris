import datetime
from typing import Dict, List
from uuid import UUID
from dataclasses import asdict
from math import ceil

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, text
from langchain.messages import HumanMessage, SystemMessage

from app.models.conversation import Conversation, ConversationMessage
from app.models.file import File
from app.models.quota import Quota
from app.core.errors import AppError
from app.core.error_registry import CONVERSATION_FORBIDDEN, FILE_NOT_FOUND, FILE_FORBIDDEN, FILE_DELETED, CONVERSATION_NOT_FOUND, FILE_NOT_READY, QUOTA_EXCEEDED_CONVERSATIONS, QUOTA_EXCEEDED_LLM_TOKENS, QUOTA_NOT_FOUND
from app.core.enums import ConversationScopeEnum, FileStatusEnum, MessageRoleEnum, AgentEventTypeEnum
from app.db.session import AgentDBSessionLocal
from app.agents.runtime_context import AgentContext
from app.agents.orchestrator import get_orchestrator
from app.agents.streaming import agent_sse_event, TokenCounterCallback
from app.agents.llms import orchestrator_llm
from app.agents.prompts import orchestrator_base
from app.schemas.chat import ConversationCreate


async def create_conversation(
    session: AsyncSession,
    *,
    user_id: UUID,
    data: ConversationCreate,
) -> Conversation:

    quota_stmt = select(Quota).where(Quota.user_id == user_id).with_for_update()
    quota = (await session.execute(quota_stmt)).scalar_one_or_none()
    if quota is None:
        raise AppError(QUOTA_NOT_FOUND)
    if quota.conversations < 1:
        raise AppError(QUOTA_EXCEEDED_CONVERSATIONS)

    if data.scope == ConversationScopeEnum.FILE:
        if data.file_id is None: # This check is for unit and integration tests, uptime validation is handled by pydantic
            raise ValueError("file_id is required for file-scoped conversations")
        f: File | None = await session.get(File, data.file_id)
        if f is None:
            raise AppError(FILE_NOT_FOUND)
        if f.user_id != user_id:
            raise AppError(FILE_FORBIDDEN)
        if f.deleted_at is not None:
            raise AppError(FILE_DELETED)
        if f.status != FileStatusEnum.READY:
            raise AppError(FILE_NOT_READY)

    conv = Conversation(user_id=user_id, scope=data.scope, file_id=data.file_id, title=data.title)
    session.add(conv)
    quota.conversations -= 1
    await session.flush([conv, quota])
    await session.refresh(conv)

    return conv

async def update_conversation_title(
    session: AsyncSession,
    *,
    user_id: UUID,
    conv_id: UUID,
    title: str,
) -> Conversation:
    conv = await session.get(Conversation, conv_id)
    if conv is None:
        raise AppError(CONVERSATION_NOT_FOUND)
    if conv.user_id != user_id:
        raise AppError(CONVERSATION_FORBIDDEN)
    
    conv.title = title.strip()
    await session.flush()
    await session.refresh(conv)
    return conv
    
async def delete_conversation(
    session: AsyncSession,
    *,
    id: UUID,
    user_id: UUID,
):
    conv = await session.get(Conversation, id)
    if conv is None:
        return
    if conv.user_id != user_id:
        raise AppError(CONVERSATION_FORBIDDEN)
    
    quota_stmt = select(Quota).where(Quota.user_id == user_id).with_for_update()
    quota = (await session.execute(quota_stmt)).scalar_one_or_none()
    if quota is None:
        raise AppError(QUOTA_NOT_FOUND)

    quota.conversations += 1
    
    # Delete related checkpoints and persisted satet from the Agent's saver
    async with AgentDBSessionLocal() as agent_session:
        await agent_session.execute(text(f"DELETE FROM checkpoint_writes WHERE thread_id = :id"), {"id": str(id)})
        await agent_session.execute(text(f"DELETE FROM checkpoint_blobs WHERE thread_id = :id"), {"id": str(id)})
        await agent_session.execute(text(f"DELETE FROM checkpoints WHERE thread_id = :id"), {"id": str(id)})
        await agent_session.commit()
    
    await session.delete(conv)
    await session.flush([conv, quota])

async def get_user_conversations(
    session: AsyncSession,
    *,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, List[Conversation] | int | bool]:

    offset = (page - 1) * page_size
    query = (
        select(Conversation)
        .filter(Conversation.user_id == user_id)
        .filter(Conversation.deleted_at.is_(None))
        .order_by(Conversation.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    res = await session.execute(query)
    results = res.scalars().all()

    total_stmt = (
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.user_id == user_id)
    )
    total = await session.scalar(total_stmt)

    return {
        "items": results,
        "page": page,
        "page_size": len(results),
        "total": total,
        "has_next": offset + page_size < total,
    }


async def get_conversation_messages(
    session: AsyncSession,
    *,
    user_id: UUID,
    conversation_id: UUID,
    limit: int = 5,
    cursor: datetime.datetime | None = None,
) -> Dict[str, List[Conversation] | str | bool]:

    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id,
        Conversation.deleted_at.is_(None),
    )
    res = await session.execute(stmt)
    conversation = res.scalar_one_or_none()
    if conversation is None:
        raise AppError(CONVERSATION_NOT_FOUND)
    
    query = (
        select(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.desc())
        .limit(limit + 1)
    )

    if cursor:
        query = query.filter(ConversationMessage.created_at < cursor)

    results = (await session.execute(query)).scalars().all()

    has_next = len(results) > limit
    items = results[:limit]

    next_cursor = items[-1].created_at if has_next else None

    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_next": has_next,
    }

async def add_message(
    session: AsyncSession,
    *,
    conversation_id: UUID,
    role: MessageRoleEnum,
    content: str,
) -> ConversationMessage:
    msg = ConversationMessage(conversation_id=conversation_id, role=role, content=content)
    session.add(msg)
    await session.execute(
        select(Conversation).where(Conversation.id == conversation_id).execution_options(populate_existing=True)
    )
    await session.flush()
    await session.refresh(msg)
    return msg

async def get_upfront_token_reservation(thread: UUID, msg: str):
    """Gets an estimate of the total tokens used for an agent run.

    Args:
        thread (UUID): the thread ID for the conversation thread
        msg (str): the new message that will be appended to the thread before getting a model response
    
    Returns:
        total_tokens_estimate (int): an integer representing a rough estimate of the total tokens that will be used for this run.
            Output tokens count is estimated based on the average message length in the thread with an overhead factor.
    """

    agent = await get_orchestrator()
    model = orchestrator_llm()
    config = {'thread_id': thread}

    state = await agent.aget_state({"configurable": config})
    messages = state.values.get("messages", [])

    # Handle newly created conversations with no messages yet
    if len(messages) == 0:
        messages.append(HumanMessage(msg))
        corrected_messages = [SystemMessage(orchestrator_base + orchestrator_base[:ceil(len(orchestrator_base) * 1.2)]), HumanMessage(msg)]
    else:
        corrected_messages = [SystemMessage(orchestrator_base + orchestrator_base[:ceil(len(orchestrator_base) * 1.2)]), *messages]

    input_tokens = ceil(model.get_num_tokens_from_messages(corrected_messages))
    output_tokens_estimate = ceil(model.get_num_tokens_from_messages(messages)/len(messages) * 1.3) # Average message length with overhead factor
    return input_tokens + output_tokens_estimate

async def get_agent_context(
    session: AsyncSession,
    *,
    user_name: str,
    conv: Conversation,
):

    if conv.scope == ConversationScopeEnum.FILE:
        f = await session.get(File, conv.file_id)
        files = [f"file name: {f.name}, file extension: {f.extension}, file id: {f.id}, file description: {f.description}, file size in bytes: {f.size_bytes}"]
        
    if conv.scope == ConversationScopeEnum.STUDIO:
        stmt = select(File).where(File.user_id == conv.user_id, File.deleted_at.is_(None))
        user_files = (await session.execute(stmt)).scalars().all()
        files = [f"file name: {f.name}, file extension: {f.extension}, file id: {f.id}, file description: {f.description}, file size in bytes: {f.size_bytes}" for f in user_files]
    return AgentContext(user_id=conv.user_id, user_name=user_name, files=files)

async def agent_streamer(
    session: AsyncSession,
    *,
    msg: str,
    user_name: str,
    conv: Conversation,
): 

    _ = await add_message(session, conversation_id=conv.id, role=MessageRoleEnum.USER, content=msg)
    upfront_total = await get_upfront_token_reservation(conv.id, msg)

    quota_stmt = select(Quota).where(Quota.user_id == conv.user_id).with_for_update()
    quota = (await session.execute(quota_stmt)).scalar_one_or_none()
    if quota is None:
        yield await agent_sse_event(type=AgentEventTypeEnum.ERROR, data=asdict(QUOTA_NOT_FOUND))
        yield await agent_sse_event(type=AgentEventTypeEnum.DONE, data={"ok": True})
        return
    if quota.llm_tokens < upfront_total:
        yield await agent_sse_event(type=AgentEventTypeEnum.ERROR, data=asdict(QUOTA_EXCEEDED_LLM_TOKENS))
        yield await agent_sse_event(type=AgentEventTypeEnum.DONE, data={"ok": True})
        return
    quota.llm_tokens -= upfront_total
    await session.commit()

    orchestrator = await get_orchestrator()
    complete_response = ''
    token_counter = TokenCounterCallback()
    inputs = {'messages': [{'role': 'user', 'content': msg}]}
    context = await get_agent_context(session, user_name=user_name, conv=conv)
    config = {'thread_id': conv.id, "callbacks": [token_counter]}

    async for stream_mode, data in orchestrator.astream(
        inputs,
        config,
        context=context,
        stream_mode=["messages", "updates", "custom"]
    ):
        if stream_mode == "custom":
            yield await agent_sse_event(type=AgentEventTypeEnum.TOOL, data=data)

        elif stream_mode == "updates":
            for node_name, node_state in data.items():
                if node_name == "model":
                    last_msg = node_state.get("messages", [])[-1] if node_state.get("messages") else None
                    if last_msg and hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                        yield await agent_sse_event(type=AgentEventTypeEnum.STATUS, data={"message": "calling the right tools..."})
                        
                elif node_name == "tools":
                    yield await agent_sse_event(type=AgentEventTypeEnum.STATUS, data={"message": "tool execution completed."})
        
        elif stream_mode == "messages":
            token, metadata = data
            if token.content and metadata["langgraph_node"] == "model":
                complete_response += token.content
                yield await agent_sse_event(type=AgentEventTypeEnum.TOKEN, data={"message": token.content})
            if metadata["langgraph_node"].startswith("SummarizationMiddleware"):
                yield await agent_sse_event(
                    type=AgentEventTypeEnum.STATUS, 
                    data={
                        "message": "Conversation too long (Long conversations affect accuracy and context, start a new conversation if possible). Summarizing...",
                        "alert": "long_conversation",
                    }
                )

    total_tokens = token_counter.total_tokens

    quota_stmt = select(Quota).where(Quota.user_id == conv.user_id).with_for_update()
    quota = (await session.execute(quota_stmt)).scalar_one()
    recon = max(0, quota.llm_tokens + upfront_total - total_tokens)
    quota.llm_tokens = recon
    await add_message(session, conversation_id=conv.id, role=MessageRoleEnum.ASSISTANT, content=complete_response)
    await session.commit()
    yield await agent_sse_event(
        type=AgentEventTypeEnum.DONE, 
        data={
            "ok": True, 
            "token_usage": {
                "input_tokens": token_counter.input_tokens,
                "output_tokens": token_counter.output_tokens,
                "total_tokens": token_counter.total_tokens,
            }
        }
    )
