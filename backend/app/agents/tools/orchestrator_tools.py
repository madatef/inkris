import asyncio
import base64
from io import BytesIO
from math import ceil
import random
from uuid import UUID, uuid4

from langchain.tools import tool
from langchain.messages import SystemMessage
from langsmith import traceable
from openai import AsyncOpenAI
from sqlalchemy import select
from httpx import AsyncClient

from app.agents.subagents.rag_agent import rag_agent
from app.agents.subagents.excel_agent import excel_agent
from app.agents.streaming import tool_stream_writer
from app.agents.prompts import EXCEL_AGENT_PROMPT, RAG_SYSTEM_PROMPT
from app.agents.llms import orchestrator_llm, rag_llm
from app.agents.streaming import TokenCounterCallback
from app.db.session import AsyncSessionLocal
from app.models.quota import Quota
from app.config import settings
from app.storage.s3_provider import s3_media_client_session


async def can_execute_rag(query: str, user_id: str) -> tuple[bool, str | None]:
    """Checks if the remaining LLM tokens balance is suffiecient to execute RAG agent. """
    model = rag_llm()
    messages = [SystemMessage(RAG_SYSTEM_PROMPT), SystemMessage(query)]
    input_tokens = ceil(model.get_num_tokens_from_messages(messages) * 2)
    output_tokens = 2000
    total_tokens = input_tokens + output_tokens
    try:
        async with AsyncSessionLocal() as session:
            quota_stmt = select(Quota).where(Quota.user_id ==UUID(user_id)).with_for_update()
            quota = (await session.execute(quota_stmt)).scalar_one()
            if quota.llm_tokens < total_tokens:
                return False, None
    except Exception as e:
        return False, str(e)
    return True, None

async def can_execute_excel(query: str, user_id: str) -> tuple[bool, str | None]:
    """Checks if the remaining LLM tokens balance is suffiecient to execute RAG agent. """
    model = orchestrator_llm()
    messages = [SystemMessage(EXCEL_AGENT_PROMPT), SystemMessage(query)]
    input_tokens = ceil(model.get_num_tokens_from_messages(messages) * 2)
    output_tokens = 2000
    total_tokens = input_tokens + output_tokens
    try:
        async with AsyncSessionLocal() as session:
            quota_stmt = select(Quota).where(Quota.user_id ==UUID(user_id)).with_for_update()
            quota = (await session.execute(quota_stmt)).scalar_one()
            if quota.llm_tokens < total_tokens:
                return False, None
    except Exception as e:
        return False, str(e)
    return True, None

@tool(parse_docstring=True)
@traceable(name="rag_agent")
async def invoke_rag_agent(query: str, user_id: str, file_ids: list[str] | None):
    """Invokes the RAG agent to get top-matching file content to a given query.
    
    Args:
        query: the query to use for similarity search.
        user_id: ID of the curent user.
        file_ids: the list of file IDs to limit similarity search to. Defaults to None (search across all files).
            For conversations scoped to a specific file, this CANNOT be None and MUST ONLY contain that file's ID. If the conversation is not file-scoped,
            you can exclude the files that are less likely to contain answers.

    Returns:
        A list of chunk objects with the following keys:
            - file_id
            - page: page label.
            - text: chunk text.
    """
    await tool_stream_writer("Retrieving document(s)...")
    input_msg = f"""
        User asked: {query},
        user ID: {user_id},
        file IDs: {file_ids}
    """
    can, err = await can_execute_rag(input_msg, user_id)
    if not can:
        if err is None:
            await tool_stream_writer("Quota exceeded.")
            return {"error": "Let user know tokens quota exceeded. Can't call RAG agent."}
        return {"error": f"Couldn't check user qouta. {str(err)}"}
    token_counter = TokenCounterCallback()

    try:
        res = await rag_agent.ainvoke(
            {
                'messages': [{
                    'role': 'system',
                    'content': input_msg
                }]
            },
            {"callbacks": [token_counter]}
        )
        await tool_stream_writer("Documents retrieved. Analysing content...")

        chunks = res['structured_response'].chunks

        out = [{
            'file_id': c.file_id,
            'page': c.page,
            'text': c.text,
        } for c in chunks]
    except Exception as e:
        return {"error": str(e)}
    try:
        async with AsyncSessionLocal() as session:
                quota_stmt = select(Quota).where(Quota.user_id ==UUID(user_id)).with_for_update()
                quota = (await session.execute(quota_stmt)).scalar_one()
                quota.llm_tokens = max(0, quota.llm_tokens - token_counter.total_tokens)
                await session.commit()
    except Exception:
        pass
    return out

@tool(parse_docstring=True)
@traceable(name="excel_agent")
async def invoke_excel_agent(query: str, user_id: str, file_ids: list[str]):
    """Invokes the Excel agent to fetch data relevant to a given query from excel file(s).
    
    Args:
        query: the query to use for data fetching.
        user_id: ID of the curent user.
        file_ids: the list of IDs of files that are likely to have the required data.

    Returns: the fetched data.
    """
    await tool_stream_writer("Reading sheets...")
    input_msg = f"""
        User intent: {query},
        user ID: {user_id},
        file IDs: {file_ids}
        If multiple file IDs are provided, decide which file to fetch data from by getting sheet names and previes per file.
    """
    can, err = await can_execute_excel(input_msg, user_id)
    if not can:
        if err is None:
            await tool_stream_writer("Quota exceeded.")
            return {"error": "Let user know tokens quota exceeded. Can't call Excel Agent."}
        return {"error": f"Couldn't check user qouta. {str(err)}"}
    token_counter = TokenCounterCallback()

    try:
        res = await excel_agent.ainvoke(
            {
                'messages': [{
                    'role': 'system',
                    'content': input_msg
                }]
            },
            {"callbacks": [token_counter]}
        )
        await tool_stream_writer("Data fetched. Analysing content...")

        out = res['messages'][-1].content
    except Exception as e:
        return {"error": str(e)}
    try:
        async with AsyncSessionLocal() as session:
            quota_stmt = select(Quota).where(Quota.user_id ==UUID(user_id)).with_for_update()
            quota = (await session.execute(quota_stmt)).scalar_one()
            quota.llm_tokens = max(0, quota.llm_tokens - token_counter.total_tokens)
            await session.commit()
    except Exception:
        pass
    return out

@tool(parse_docstring=True)
async def web_search(query: str, user_id: str, limit: int = 5):
    """Gets the top matching web search results for a query.

    Args:
        query (str): the search query.
        user_id (str): ID of the user making the request. Used for auditing and qouta accounting.
        limit (int): the number of results to fetch. Defaults to 5.

    Returns:
        a list of dicts with title, link, snippet, date, rating, and rating_count 
    """
    await tool_stream_writer("Searching the web...")
    async with AsyncSessionLocal() as session:
        quota_stmt = select(Quota).where(Quota.user_id ==UUID(user_id)).with_for_update()
        quota = (await session.execute(quota_stmt)).scalar_one()
        if quota.web_searches < 1:
            await tool_stream_writer("Quota exceeded.")
            return {"error": "User has exceeded web search quota."}
        quota.web_searches -= 1
        await session.commit()
    
    client = AsyncClient()
    payload = {
        "q": query,
        "num": limit,
    }
    headers = {
        "X-API-KEY": settings.SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    try:
        results = (await client.post("https://google.serper.dev/search", json=payload, headers=headers)).json()
        await tool_stream_writer("Parsing search results...")
        out = [
            {
                "title": item.get('title', ""),
                "link": item.get('link', ""),
                "snippet": item.get('snippet', ""),
                "date": item.get('date', ""),
                "rating": item.get('rating', ""),
                "rating_count": item.get('ratingCount', ""),
            } for item in results.get("organic", [])
        ]

        return out
    except Exception as e:
        async with AsyncSessionLocal() as session:
            quota_stmt = select(Quota).where(Quota.user_id ==UUID(user_id)).with_for_update()
            quota = (await session.execute(quota_stmt)).scalar_one()
            quota.web_searches += 1
            await session.commit()
        return {"error": str(e)}

@tool(parse_docstring=True)
async def web_scraper(url: str, user_id: str):
    """Gets the content of a website using its url.

    Args:
        url (str): the url of the website to scrape.
        user_id (str): ID of the user making the request.

    Returns:
        a string of the page content formatted as markdown
    """
    await tool_stream_writer("Fetching page content...")
    async with AsyncSessionLocal() as session:
        quota_stmt = select(Quota).where(Quota.user_id == user_id).with_for_update()
        quota = (await session.execute(quota_stmt)).scalar_one()
        if quota.web_scraping < 1:
            await tool_stream_writer("Quota exceeded.")
            return "error: user has exceeded web scraping quota."
        quota.web_scraping -= 1
        await session.commit()
    
    client = AsyncClient()
    headers = {
        'Authorization': f"Bearer {settings.JINA_API_KEY}",
        'X-Return-Format': 'markdown',
    }
    try:
        res = await client.get(f"https://r.jina.ai/{url}", headers=headers)
        await tool_stream_writer("Fetched page. Analysing content...")
        return res.text
    except Exception as e:
        async with AsyncSessionLocal() as session:
            quota_stmt = select(Quota).where(Quota.user_id == user_id).with_for_update()
            quota = (await session.execute(quota_stmt)).scalar_one()
            quota.web_scraping += 1
            await session.commit()
        return f"error: {str(e)}"

@tool(parse_docstring=True)
async def generate_image(
    user_id: str,
    prompt: str,
    background: str = 'auto',
    output_format: str = 'png',
    quality: str = 'auto',
    size: str = 'auto',
):
    """Generates an image from a text prompt.

    Args:
        user_id (str): ID of the user making the request.
        prompt (str): a text description of what to generate.
        background (Literal['transparent', 'opaque', 'auto']): defaults to auto.
        output_format (Literal['png', 'jpeg', 'webp']): defaults to png.
        quality (Literal['low', 'medium', 'high', 'auto']): defaults to auto.
        size (Literal['auto', '1024x1024', '1536x1024', '1024x1536', '256x256', '512x512', '1792x1024', '1024x1792']): defaults to auto.
    
    Returns:
        a string representing the URL of the generated image.
    """
    await tool_stream_writer("Generating image...")
    async with AsyncSessionLocal() as session:
        quota_stmt = select(Quota).where(Quota.user_id == user_id).with_for_update()
        quota = (await session.execute(quota_stmt)).scalar_one()
        if quota.image_generations < 1:
            await tool_stream_writer("Quota exceeded.")
            return "error: user has exceeded image generation quota."
        quota.image_generations -= 1
        await session.commit()
    
    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        result = await client.images.generate(
            model="gpt-image-1.5",
            prompt=prompt,
            background=background,
            output_format=output_format,
            quality=quality,
            size=size,
        )

        await tool_stream_writer("Image generatined. Parsing output...")
        image_b64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_b64)
        buf = BytesIO(image_bytes)
        buf.seek(0)
        
        key=f"{uuid4()}.{output_format}"
        await tool_stream_writer("Saving image...")
        async with  s3_media_client_session.client('s3') as s3:
            await s3.upload_fileobj(
                Fileobj=buf,
                Bucket=settings.AWS_S3_MEDIA_BUCKET,
                Key=key,
                ExtraArgs={
                    "ContentType": f"image/{output_format}",
                },
            )

        return f"https://{settings.AWS_S3_MEDIA_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
    except Exception as e:
        async with AsyncSessionLocal() as session:
            quota_stmt = select(Quota).where(Quota.user_id == user_id).with_for_update()
            quota = (await session.execute(quota_stmt)).scalar_one()
            quota.image_generations += 1
            await session.commit()
        return f"error: {str(e)}"

@tool(parse_docstring=True)
async def generate_video(
    prompt:str,
    user_id: str,
    seconds: str = '8',
    size: str = '720x1280',
):
    """Generates a video from a text prompt.

    Args:
        user_id (str): ID of the user making the request.
        prompt (str): a text description of what to generate.
        seconds (Literal['4', '8', '12']): defaults to 8.
        size (Literal['720x1280', '1280x720', '1024x1792', '1792x1024']): defaults to 720x1280.
    
    Returns:
        a string representing the URL of the generated video.
    """
    await tool_stream_writer('Starting video generation job...')
    async with AsyncSessionLocal() as session:
        quota_stmt = select(Quota).where(Quota.user_id == user_id).with_for_update()
        quota = (await session.execute(quota_stmt)).scalar_one()
        if quota.video_generations < 1:
            await tool_stream_writer("Quota exceeded.")
            return "error: user has exceeded video generation quota."
        quota.video_generations -= 1
        await session.commit()

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    video_job = await client.videos.create(
        prompt=prompt,
        model='sora-2',
        seconds=seconds,
        size=size,
        timeout=10*60, # 10 mins
    )
    video_id = video_job.id
    status = video_job.status
    await tool_stream_writer(f'Video job started. Video ID: {video_id}, status: {status}')

    start_time = asyncio.get_event_loop().time()
    attempt = 0

    while status not in ("completed", "failed"):
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed > 600:
            await tool_stream_writer('Video generation process timed out.')
            async with AsyncSessionLocal() as session:
                quota_stmt = select(Quota).where(Quota.user_id == user_id).with_for_update()
                quota = (await session.execute(quota_stmt)).scalar_one()
                quota.video_generations += 1
                await session.commit()
            return 'Video generation process timed out.'

        # Exponential backoff with jitter
        delay = min(
            30,
            2 * (2 ** attempt)
        )
        delay = delay * (0.5 + random.random() / 2)

        await asyncio.sleep(delay)

        retrieve_job = await client.videos.retrieve(video_id)
        status = retrieve_job.status
        progress = retrieve_job.progress
        await tool_stream_writer(f'Generating video. Progress: {progress}% ...')

        attempt += 1

        if status == "failed":
            await tool_stream_writer(
                f"Video generation failed: {retrieve_job.error}"
            )
            async with AsyncSessionLocal() as session:
                quota_stmt = select(Quota).where(Quota.user_id == user_id).with_for_update()
                quota = (await session.execute(quota_stmt)).scalar_one()
                quota.video_generations += 1
                await session.commit()
            
            return f"Video generation failed: {retrieve_job.error}"

    await tool_stream_writer(f'Video generated. Saving to cloud...')
    key = f"{video_id}.mp4"
    MULTIPART_CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB
    MAX_UPLOAD_RETRIES = 3

    async with s3_media_client_session.client('s3') as s3:

        for retry_attempt in range(MAX_UPLOAD_RETRIES):
            parts = []
            part_number = 1

            try:
                multipart = await s3.create_multipart_upload(
                    Bucket=settings.AWS_S3_MEDIA_BUCKET,
                    Key=key,
                    ContentType="video/mp4",
                )
                upload_id = multipart["UploadId"]
                buffer = bytearray()
                
                # Use with_streaming_response to get the streaming response
                async with client.videos.with_streaming_response.download_content(video_id) as content:
                    async for chunk in content.iter_bytes(MULTIPART_CHUNK_SIZE):
                        buffer.extend(chunk)

                        while len(buffer) >= MULTIPART_CHUNK_SIZE:
                            part = bytes(buffer[:MULTIPART_CHUNK_SIZE])
                            del buffer[:MULTIPART_CHUNK_SIZE]

                            response = await s3.upload_part(
                                Bucket=settings.AWS_S3_MEDIA_BUCKET,
                                Key=key,
                                PartNumber=part_number,
                                UploadId=upload_id,
                                Body=part,
                            )

                            parts.append({
                                "ETag": response["ETag"],
                                "PartNumber": part_number,
                            })

                            part_number += 1

                    # Upload remaining buffer
                    if buffer:
                        response = await s3.upload_part(
                            Bucket=settings.AWS_S3_MEDIA_BUCKET,
                            Key=key,
                            PartNumber=part_number,
                            UploadId=upload_id,
                            Body=bytes(buffer),
                        )

                        parts.append({
                            "ETag": response["ETag"],
                            "PartNumber": part_number,
                        })

                # Complete multipart upload
                parts.sort(key=lambda x: x["PartNumber"])
                await s3.complete_multipart_upload(
                    Bucket=settings.AWS_S3_MEDIA_BUCKET,
                    Key=key,
                    UploadId=upload_id,
                    MultipartUpload={"Parts": parts},
                )
            except Exception as e:
                # Abort upload if anything fails
                if upload_id:
                    await s3.abort_multipart_upload(
                        Bucket=settings.AWS_S3_MEDIA_BUCKET,
                        Key=key,
                        UploadId=upload_id,
                    )
                await tool_stream_writer(f'Failed to save video to cloud. Retrying {retry_attempt}/{MAX_UPLOAD_RETRIES}...')
                if retry_attempt > 2:
                    return f"Couldn't save video to cloud: {str(e)}"

    return f"https://{settings.AWS_S3_MEDIA_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


ORCHESTRATOR_TOOLS = [invoke_rag_agent, invoke_excel_agent, web_search, web_scraper, generate_image, generate_video]
__all__ = [ORCHESTRATOR_TOOLS]