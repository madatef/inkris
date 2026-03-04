from langchain.tools import tool

from app.vector_store.qdrant import qdrant_store
from app.services.transformers.embedders import openai_text_small
from app.vector_store.base import VectorFilter
from app.config import settings


@tool(parse_docstring=True)
async def get_vector_points(query: str, user_id: str, limit: int = 5, file_ids: list[str] | None = None):
    """Gets the user's document chunks matching a given query using semantic similarity.

    Args:
        query (str): the query to use for similarity search.
        user_id (str): the user's ID to whose files the search is scoped.
        limit (int): the number of top-matching vector points to retrieve. Defaults to 5.
        file_ids (list[str] | None): used to filter the search and scope it to a specific file chunks. Defaults to None (search across all user files).

    Returns:
        a list of dicts with the following keys:
        - file_id: the file from which the text was extracted
        - page: the specific page label in the file where the text lies
        - prev_point_id: the ID of the previous vector point. Used to retrieve the previous text chunk if needed.
        - next_point_id: the ID of the next point. Used to retrieve the next text chunk if needed.
        - text: the actual text extracted from the file.
    """

    filters = [VectorFilter(key='user_id', values=[user_id])]
    if file_ids is not None:
        filters.append(VectorFilter(key='file_id', values=[id for id in file_ids]))

    vector = openai_text_small.embed_text(query)
    res = await qdrant_store.search(
        collection=settings.QDRANT_COLLECTION,
        vector=vector,
        limit=limit,
        filters=filters,
    )
    result = res.points
    out = [
        {
            'file_id': p.payload.get('file_id'),
            'page': p.payload.get('page_label'),
            'prev_point_id': p.payload.get('prev_point_id'),
            'next_point_id': p.payload.get('next_point_id'),
            'text': p.payload.get('text'),
        } for p in result
    ]
    return out

@tool(parse_docstring=True)
async def get_points_by_ids(ids: list[str]):
    """Gets the document chunks by vector point ID.

    Args:
        ids (list[str]): a list of IDs of the vector points to be retrieved.

    Returns:
        a list of dicts with the following keys:
        - page: the specific page label in the file where the text lies
        - prev_point_id: the ID of the previous vector point. Used to retrieve the previous text chunk if needed.
        - next_point_id: the ID of the next point. Used to retrieve the next text chunk if needed.
        - text: the actual text extracted from the file.
    """
    points = await qdrant_store.get_points_by_id(collection=settings.QDRANT_COLLECTION, ids=ids)
    out = [
        {
            "page": p.payload.get("page_label"),
            "prev_point_id": p.payload.get("prev_point_id"),
            "next_point_id": p.payload.get("next_point_id"),
            "text": p.payload.get("text"),
        } for p in points
    ]
    return out

@tool(parse_docstring=True)
async def get_points_by_page_label(page_label: str, file_id: str):
    """Gets all the document chunks of a specific page in a specific file.

    Args:
        page_label (str): the page number/label
        file_id (str): the file to be searched

    Returns:
        a list of dicts with the following keys:
        - prev_point_id: the ID of the previous vector point. Used to retrieve the previous text chunk if needed.
        - next_point_id: the ID of the next point. Used to retrieve the next text chunk if needed.
        - text: the actual text extracted from the file.
    """
    points = (await qdrant_store.get_points_by_page_label(collection=settings.QDRANT_COLLECTION, page_label=page_label, file_id=file_id)).points
    out = [
        {
            "prev_point_id": p.payload.get("prev_point_id"),
            "next_point_id": p.payload.get("next_point_id"),
            "text": p.payload.get("text"),
        } for p in points
    ]
    return out

RAG_TOOLS = [get_vector_points, get_points_by_ids, get_points_by_page_label]