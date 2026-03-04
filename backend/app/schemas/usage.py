from pydantic import BaseModel

class UserQuota(BaseModel):
    files: int
    file_processing: int
    storage_bytes: int
    conversations: int
    web_searches: int
    web_scraping: int
    image_generations: int
    video_generations: int
    llm_tokens: int

    class Config:
        from_attributes = True
        populate_by_name = True