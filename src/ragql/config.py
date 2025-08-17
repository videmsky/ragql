"""Configuration management for RAG-QL application."""

import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
    
    # Ensure HF_TOKEN is available for Hugging Face tokenizer downloads
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        os.environ["HF_TOKEN"] = hf_token
except ImportError:
    pass


@dataclass
class Config:
    """Configuration settings for the RAG-QL application."""
    
    mistral_api_key: str
    neon_connection_string: str
    collection_name: str = "text-to-sql-context"
    embedding_model: str = "mistral-embed"
    chat_model: str = "mistral-medium"
    max_schema_results: int = 5
    max_query_examples: int = 3
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        neon_connection_string = os.getenv("NEON_CONNECTION_STRING")
        
        if not mistral_api_key:
            raise ValueError(
                "MISTRAL_API_KEY environment variable is required. "
                "Get your API key from https://console.mistral.ai/"
            )
        
        if not neon_connection_string:
            raise ValueError(
                "NEON_CONNECTION_STRING environment variable is required. "
                "Get your connection string from https://console.neon.tech/"
            )
        
        return cls(
            mistral_api_key=mistral_api_key,
            neon_connection_string=neon_connection_string,
            collection_name=os.getenv("COLLECTION_NAME", "text-to-sql-context"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "mistral-embed"),
            chat_model=os.getenv("CHAT_MODEL", "mistral-medium"),
            max_schema_results=int(os.getenv("MAX_SCHEMA_RESULTS", "5")),
            max_query_examples=int(os.getenv("MAX_QUERY_EXAMPLES", "3")),
        )
    
    @property
    def data_dir(self) -> Path:
        """Get the data directory path."""
        return Path(__file__).parent.parent.parent / "data"
    
    @property
    def schema_file(self) -> Path:
        """Get the Northwind schema file path."""
        return self.data_dir / "northwind-schema.sql"
    
    @property
    def queries_file(self) -> Path:
        """Get the Northwind queries file path."""
        return self.data_dir / "northwind-queries.jsonl"
    
    def validate(self) -> None:
        """Validate configuration settings."""
        if not self.mistral_api_key.strip():
            raise ValueError("Mistral API key cannot be empty")
        
        if not self.neon_connection_string.strip():
            raise ValueError("Neon connection string cannot be empty")
        
        if not self.neon_connection_string.startswith(("postgres://", "postgresql://")):
            raise ValueError("Neon connection string must be a valid PostgreSQL URL")
        
        if self.max_schema_results <= 0:
            raise ValueError("max_schema_results must be positive")
        
        if self.max_query_examples <= 0:
            raise ValueError("max_query_examples must be positive")