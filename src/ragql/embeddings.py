"""Embeddings and vector store management for RAG-QL application."""

import json
import logging
import os
import warnings
from typing import List, Dict, Any
from pathlib import Path

# Suppress the Hugging Face tokenizer warning at the source
warnings.filterwarnings("ignore", message="Could not download mistral tokenizer from Huggingface*")

from langchain_core.documents import Document
from langchain_mistralai.embeddings import MistralAIEmbeddings
from langchain_postgres.vectorstores import PGVector

from .config import Config
from .database import DatabaseManager

logger = logging.getLogger(__name__)


class EmbeddingsManager:
    """Manages embeddings generation and vector store operations."""
    
    def __init__(self, config: Config, db_manager: DatabaseManager):
        """Initialize embeddings manager."""
        self.config = config
        self.db_manager = db_manager
        self._embedding_model = None
        self._vector_store = None
    
    @property
    def embedding_model(self) -> MistralAIEmbeddings:
        """Get or create embedding model."""
        if self._embedding_model is None:
            # Check HF_TOKEN availability and log status
            hf_token = os.getenv("HF_TOKEN")
            if hf_token:
                logger.info("HF_TOKEN found - using optimized Mistral tokenizer for embeddings")
            else:
                logger.info("HF_TOKEN not found - using fallback tokenizer (reduced batching performance)")
                logger.info("To improve performance: Get a free token at https://huggingface.co/settings/tokens")
            
            self._embedding_model = MistralAIEmbeddings(
                model=self.config.embedding_model,
                api_key=self.config.mistral_api_key
            )
        return self._embedding_model
    
    @property
    def vector_store(self) -> PGVector:
        """Get or create vector store."""
        if self._vector_store is None:
            self._vector_store = PGVector(
                embeddings=self.embedding_model,
                connection=self.db_manager.engine,
                use_jsonb=True,
                collection_name=self.config.collection_name,
            )
        return self._vector_store
    
    def setup_vector_store(self) -> None:
        """Initialize vector store and populate with data."""
        logger.info("Setting up vector store...")
        
        self._populate_ddl_embeddings()
        self._populate_query_embeddings()
        
        logger.info("Vector store setup completed")
    
    def _populate_ddl_embeddings(self) -> None:
        """Populate vector store with DDL statement embeddings."""
        ddl_statements = self.db_manager.get_ddl_statements()
        
        docs = [
            Document(
                page_content=stmt, 
                metadata={"id": f"ddl-{i}", "topic": "ddl"}
            )
            for i, stmt in enumerate(ddl_statements)
        ]
        
        if docs:
            doc_ids = [doc.metadata["id"] for doc in docs]
            self.vector_store.add_documents(docs, ids=doc_ids)
            logger.info(f"Added {len(docs)} DDL statements to vector store")
    
    def _populate_query_embeddings(self) -> None:
        """Populate vector store with sample query embeddings."""
        if not self.config.queries_file.exists():
            logger.warning(f"Queries file not found: {self.config.queries_file}")
            return
        
        docs = []
        try:
            with open(self.config.queries_file) as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if line:
                        docs.append(Document(
                            page_content=line,
                            metadata={"id": f"query-{i}", "topic": "query"}
                        ))
            
            if docs:
                doc_ids = [doc.metadata["id"] for doc in docs]
                self.vector_store.add_documents(docs, ids=doc_ids)
                logger.info(f"Added {len(docs)} sample queries to vector store")
        
        except Exception as e:
            logger.error(f"Failed to populate query embeddings: {e}")
            raise
    
    def search_similar_ddl(self, query: str, k: int = None) -> List[Document]:
        """Search for similar DDL statements."""
        k = k or self.config.max_schema_results
        
        try:
            results = self.vector_store.similarity_search(
                query=query,
                k=k,
                filter={"topic": {"$eq": "ddl"}}
            )
            logger.info(f"Found {len(results)} similar DDL statements")
            return results
        
        except Exception as e:
            logger.error(f"DDL similarity search failed: {e}")
            return []
    
    def search_similar_queries(self, query: str, k: int = None) -> List[Document]:
        """Search for similar query examples."""
        k = k or self.config.max_query_examples
        
        try:
            results = self.vector_store.similarity_search(
                query=query,
                k=k,
                filter={"topic": {"$eq": "query"}}
            )
            logger.info(f"Found {len(results)} similar query examples")
            return results
        
        except Exception as e:
            logger.error(f"Query similarity search failed: {e}")
            return []
    
    def get_context_for_query(self, query: str) -> Dict[str, Any]:
        """Get relevant context (DDL + examples) for a natural language query."""
        ddl_docs = self.search_similar_ddl(query)
        query_docs = self.search_similar_queries(query)
        
        schema = ""
        for doc in ddl_docs:
            schema += doc.page_content + "\n\n"
        
        examples = ""
        for doc in query_docs:
            try:
                text_sql_pair = json.loads(doc.page_content)
                examples += f"Question: {text_sql_pair['question']}\n"
                examples += f"SQL: {text_sql_pair['query']}\n\n"
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse query example: {e}")
                continue
        
        return {
            "schema": schema.strip(),
            "examples": examples.strip(),
            "ddl_count": len(ddl_docs),
            "example_count": len(query_docs)
        }
    
    def clear_vector_store(self) -> None:
        """Clear all documents from vector store."""
        try:
            self.vector_store.delete_collection()
            logger.info("Vector store cleared")
        except Exception as e:
            logger.error(f"Failed to clear vector store: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about the vector store collection."""
        try:
            ddl_results = self.vector_store.similarity_search(
                query="CREATE TABLE",
                k=1000,
                filter={"topic": {"$eq": "ddl"}}
            )
            
            query_results = self.vector_store.similarity_search(
                query="SELECT",
                k=1000, 
                filter={"topic": {"$eq": "query"}}
            )
            
            return {
                "ddl_count": len(ddl_results),
                "query_count": len(query_results),
                "total_count": len(ddl_results) + len(query_results)
            }
        
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"ddl_count": 0, "query_count": 0, "total_count": 0}