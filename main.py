"""Main application entry point for RAG-QL text-to-SQL system."""

import os
import logging
import sys
import warnings
from pathlib import Path

# Load environment variables early to ensure HF_TOKEN is available
try:
    from dotenv import load_dotenv
    load_dotenv()
    # Ensure HF_TOKEN is set for Hugging Face tokenizer downloads
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        os.environ["HF_TOKEN"] = hf_token
except ImportError:
    pass

# Suppress the Hugging Face tokenizer warning for cleaner output
# The actual tokenizer status will be logged informatively by the embeddings manager
warnings.filterwarnings("ignore", message="Could not download mistral tokenizer from Huggingface*")

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('ragql.log')
        ]
    )

def main():
    """Main application entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        from src.ragql.config import Config
        from src.ragql.database import DatabaseManager
        from src.ragql.embeddings import EmbeddingsManager
        from src.ragql.query import QueryGenerator
        
        logger.info("Starting RAG-QL Text-to-SQL System")
        
        config = Config.from_env()
        config.validate()
        logger.info("Configuration loaded and validated")
        
        db_manager = DatabaseManager(config)
        if not db_manager.test_connection():
            logger.error("Database connection failed")
            return 1
        
        logger.info("Setting up database schema...")
        db_manager.setup_schema()
        
        logger.info("Initializing embeddings manager...")
        embeddings_manager = EmbeddingsManager(config, db_manager)
        embeddings_manager.setup_vector_store()
        
        logger.info("Initializing query generator...")
        query_generator = QueryGenerator(config, embeddings_manager)
        
        sample_question = "Find the employee who has processed the most orders and display their full name and the number of orders they have processed?"
        
        logger.info(f"Testing with sample question: {sample_question}")
        result = query_generator.generate_with_execution(sample_question)
        
        print("\n" + "="*60)
        print("SAMPLE QUERY RESULTS")
        print("="*60)
        print(f"Question: {result['question']}")
        print(f"Generated SQL: {result['sql']}")
        
        if result.get('results'):
            print(f"Results ({result['row_count']} rows):")
            for i, row in enumerate(result['results'][:5]):  # Show first 5 rows
                print(f"  {i+1}: {row}")
        elif result.get('error'):
            print(f"Error: {result['error']}")
        
        print("="*60)
        logger.info("RAG-QL system initialized successfully")
        
        return 0
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
