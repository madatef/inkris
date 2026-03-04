from typing import List

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Document

from app.services.transformers.base import Chunker, Embedder, FilePage
from app.vector_store.base import VectorPoint, VectorPayload
from app.core.enums import LlamaIndexSplitterEnum, ChunkTypeEnum, VectorPointRelationEnum

class LlamaIndexChunker(Chunker):
    def __init__(self, *, chunk_size: int, overlap: int):
        super().__init__(chunk_size=chunk_size, overlap=overlap)
        self.splitters = {
            LlamaIndexSplitterEnum.SENTENCE: self.__get_sentence_splitter(),
            # add hierarchical node parser later
        }
    
    def __get_sentence_splitter(self):
        return SentenceSplitter(
            separator=". ",
            chunk_size=self.chunk_size,
            chunk_overlap=self.overlap,
            paragraph_separator="\n\n",
            include_prev_next_rel=True,
            include_metadata=True,
        )
    
    def __docs_to_nodes(self, docs: List[Document], splitter):
        if isinstance(splitter, SentenceSplitter):
            return splitter.get_nodes_from_documents(docs)
        else:
            pass # implement later for Hierarchical node parser

    def pages_to_points(
        self, 
        *, 
        pages: List[FilePage], 
        splitter: LlamaIndexSplitterEnum, 
        embedder: Embedder,
    ) -> List[VectorPoint]:
        splitter = self.splitters[splitter]
        documents = [
            Document(
                text=page.text,
                metadata=page.metadata.model_dump(),
            )
            for page in pages
        ]
        nodes = self.__docs_to_nodes(documents, splitter)
        points = [
                VectorPoint(
                    id=node.id_,
                    vector=embedder.embed_text(node.text),
                    payload=VectorPayload(
                        user_id=node.metadata.get("user_id"),
                        file_id=node.metadata.get("file_id"),
                        page_label=node.metadata.get("page_label"),
                        parent_id=node.relationships.get(VectorPointRelationEnum.PARENT).node_id if node.relationships.get(VectorPointRelationEnum.PARENT) else None,
                        prev_point_id=node.relationships.get(VectorPointRelationEnum.PREVIOUS).node_id if node.relationships.get(VectorPointRelationEnum.PREVIOUS) else None,
                        next_point_id=node.relationships.get(VectorPointRelationEnum.NEXT).node_id if node.relationships.get(VectorPointRelationEnum.NEXT) else None,
                        start_char_idx=node.start_char_idx,
                        end_char_idx=node.end_char_idx,
                        text=node.text,
                        chunk_type=ChunkTypeEnum.TEXT,
                    )
                ) for node in nodes
        ]
        return points

llamaindex_sentence_splitter = LlamaIndexChunker(chunk_size=512, overlap=50) 