"""Query generation module for text-to-SQL conversion."""

import re
import logging
from typing import Dict, Any, Optional, Tuple

from langchain_mistralai.chat_models import ChatMistralAI
from langchain_core.messages import HumanMessage

from .config import Config
from .embeddings import EmbeddingsManager

logger = logging.getLogger(__name__)


class QueryGenerator:
    """Generates SQL queries from natural language using RAG approach."""
    
    def __init__(self, config: Config, embeddings_manager: EmbeddingsManager):
        """Initialize query generator."""
        self.config = config
        self.embeddings_manager = embeddings_manager
        self._chat_model = None
        
        self.prompt_template = """
You are an AI assistant that converts natural language questions into SQL queries. To do this, you will be provided with three key pieces of information:

1. Some DDL statements describing tables, columns and indexes in the database:
<schema>
{SCHEMA}
</schema>

2. Some example pairs demonstrating how to convert natural language text into a corresponding SQL query for this schema:  
<examples>
{EXAMPLES}
</examples>

3. The actual natural language question to convert into an SQL query:
<question>
{QUESTION}
</question>

Follow the instructions below:
1. Your task is to generate an SQL query that will retrieve the data needed to answer the question, based on the database schema. 
2. First, carefully study the provided schema and examples to understand the structure of the database and how the examples map natural language to SQL for this schema.
3. Your answer should have two parts: 
- Inside <scratchpad> XML tag, write out step-by-step reasoning to explain how you are generating the query based on the schema, example, and question. 
- Then, inside <sql> XML tag, output your generated SQL. 
"""
    
    @property
    def chat_model(self) -> ChatMistralAI:
        """Get or create chat model."""
        if self._chat_model is None:
            self._chat_model = ChatMistralAI(
                api_key=self.config.mistral_api_key,
                model=self.config.chat_model
            )
        return self._chat_model
    
    def generate_sql(self, question: str) -> Dict[str, Any]:
        """Generate SQL query from natural language question."""
        logger.info(f"Generating SQL for question: {question}")
        
        try:
            context = self.embeddings_manager.get_context_for_query(question)
            
            if not context["schema"] and not context["examples"]:
                logger.warning("No relevant context found for query")
                return {
                    "question": question,
                    "sql": None,
                    "error": "No relevant schema or examples found",
                    "context": context
                }
            
            prompt = self.prompt_template.format(
                QUESTION=question,
                SCHEMA=context["schema"],
                EXAMPLES=context["examples"]
            )
            
            response = self._call_llm(prompt)
            sql_query = self._extract_sql(response.content)
            
            if not sql_query:
                logger.error("Failed to extract SQL from LLM response")
                return {
                    "question": question,
                    "sql": None,
                    "error": "Failed to extract SQL from response",
                    "context": context,
                    "raw_response": response.content
                }
            
            logger.info("SQL generation successful")
            return {
                "question": question,
                "sql": sql_query,
                "error": None,
                "context": context,
                "raw_response": response.content
            }
        
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return {
                "question": question,
                "sql": None,
                "error": str(e),
                "context": {},
                "raw_response": None
            }
    
    def _call_llm(self, prompt: str) -> Any:
        """Call the Mistral AI chat model."""
        try:
            response = self.chat_model.invoke([
                HumanMessage(content=prompt)
            ])
            return response
        
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise
    
    def _extract_sql(self, response_content: str) -> Optional[str]:
        """Extract SQL query from LLM response."""
        sql_match = re.search(r"<sql>(.*?)</sql>", response_content, re.DOTALL)
        if sql_match:
            sql = sql_match.group(1).strip()
            sql = re.sub(r'^```sql\s*', '', sql)
            sql = re.sub(r'\s*```$', '', sql)
            return sql
        
        logger.warning("Could not find SQL in response")
        return None
    
    def _extract_reasoning(self, response_content: str) -> Optional[str]:
        """Extract reasoning from LLM response."""
        reasoning_match = re.search(r"<scratchpad>(.*?)</scratchpad>", response_content, re.DOTALL)
        if reasoning_match:
            return reasoning_match.group(1).strip()
        return None
    
    def generate_and_validate_sql(self, question: str, validate: bool = True) -> Dict[str, Any]:
        """Generate SQL query and optionally validate it."""
        result = self.generate_sql(question)
        
        if result["sql"] and validate:
            try:
                from .database import DatabaseManager
                db_manager = DatabaseManager(self.config)
                
                is_valid = db_manager.validate_query(result["sql"])
                result["is_valid"] = is_valid
                
                if not is_valid:
                    result["error"] = "Generated SQL query failed validation"
                    logger.warning(f"Generated SQL failed validation: {result['sql']}")
            
            except Exception as e:
                result["is_valid"] = False
                result["validation_error"] = str(e)
                logger.error(f"Query validation error: {e}")
        
        return result
    
    def generate_with_execution(self, question: str) -> Dict[str, Any]:
        """Generate SQL query and execute it."""
        result = self.generate_and_validate_sql(question)
        
        if result["sql"] and result.get("is_valid", True):
            try:
                from .database import DatabaseManager
                db_manager = DatabaseManager(self.config)
                
                query_results = db_manager.execute_query(result["sql"])
                result["results"] = query_results
                result["row_count"] = len(query_results)
                
                logger.info(f"Query executed successfully, returned {len(query_results)} rows")
            
            except Exception as e:
                result["execution_error"] = str(e)
                result["results"] = []
                result["row_count"] = 0
                logger.error(f"Query execution failed: {e}")
        
        return result
    
    def batch_generate_sql(self, questions: list[str]) -> list[Dict[str, Any]]:
        """Generate SQL for multiple questions."""
        results = []
        
        for i, question in enumerate(questions):
            logger.info(f"Processing question {i+1}/{len(questions)}")
            result = self.generate_sql(question)
            results.append(result)
        
        logger.info(f"Batch processing completed: {len(results)} questions processed")
        return results