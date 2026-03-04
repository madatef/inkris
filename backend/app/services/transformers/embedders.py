from typing import List

from openai import OpenAI

from app.services.transformers.base import Embedder
from app.config import settings

class OpenAIEmbedder(Embedder):
    def __init__(self, model: str, dimensions: int):
        super().__init__(model)
        self.dimensions = dimensions
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def embed_text(self, text: str) -> List[float]:
        response = self.client.embeddings.create(input=text, model=self.model, dimensions=self.dimensions)
        return response.data[0].embedding


openai_text_small = OpenAIEmbedder(model="text-embedding-3-small", dimensions=1536)