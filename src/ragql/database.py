"""Database management for RAG-QL application."""

import logging
from pathlib import Path
from typing import List, Optional, Any, Dict
import sqlalchemy
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.exc import SQLAlchemyError

from .config import Config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, config: Config):
        """Initialize database manager with configuration."""
        self.config = config
        self._engine: Optional[Engine] = None
    
    @property
    def engine(self) -> Engine:
        """Get or create database engine."""
        if self._engine is None:
            # Convert postgresql:// URL to use psycopg driver explicitly
            connection_string = self.config.neon_connection_string
            if connection_string.startswith("postgresql://"):
                connection_string = connection_string.replace("postgresql://", "postgresql+psycopg://", 1)
            elif connection_string.startswith("postgres://"):
                connection_string = connection_string.replace("postgres://", "postgresql+psycopg://", 1)
            
            self._engine = create_engine(
                url=connection_string,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=False
            )
        return self._engine
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def setup_schema(self) -> None:
        """Setup the Northwind database schema."""
        if not self.config.schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {self.config.schema_file}")
        
        try:
            with self.engine.connect() as conn:
                with open(self.config.schema_file) as f:
                    schema_sql = f.read()
                
                conn.execute(text(schema_sql))
                conn.commit()
                logger.info("Database schema setup completed")
        
        except SQLAlchemyError as e:
            logger.error(f"Failed to setup database schema: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error setting up schema: {e}")
            raise
    
    def get_ddl_statements(self) -> List[str]:
        """Extract DDL statements from schema file."""
        if not self.config.schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {self.config.schema_file}")
        
        statements = []
        current_stmt = ""
        
        try:
            with open(self.config.schema_file) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("--"):
                        continue
                    
                    current_stmt += line + " "
                    if ";" in line:
                        stmt = current_stmt.strip()
                        if stmt.startswith(("CREATE", "ALTER")):
                            statements.append(stmt)
                        current_stmt = ""
            
            logger.info(f"Extracted {len(statements)} DDL statements")
            return statements
        
        except Exception as e:
            logger.error(f"Failed to extract DDL statements: {e}")
            raise
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                rows = [dict(row._mapping) for row in result]
                logger.info(f"Query executed successfully, returned {len(rows)} rows")
                return rows
        
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def validate_query(self, query: str) -> bool:
        """Validate SQL query without executing it."""
        query = query.strip().upper()
        
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
        for keyword in dangerous_keywords:
            if query.startswith(keyword):
                logger.warning(f"Query contains potentially dangerous keyword: {keyword}")
                return False
        
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"EXPLAIN {query}"))
            return True
        
        except SQLAlchemyError as e:
            logger.error(f"Query validation failed: {e}")
            return False
    
    def get_table_info(self, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get information about database tables."""
        if table_name:
            query = """
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = :table_name
            ORDER BY ordinal_position
            """
            params = {"table_name": table_name}
        else:
            query = """
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
            """
            params = {}
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params)
                return [dict(row._mapping) for row in result]
        
        except SQLAlchemyError as e:
            logger.error(f"Failed to get table info: {e}")
            return []
    
    def close(self) -> None:
        """Close database engine."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            logger.info("Database connection closed")