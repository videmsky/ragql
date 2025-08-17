# RAG-QL: Text-to-SQL with Mistral AI and Neon PostgreSQL

A RAG (Retrieval Augmented Generation) system that converts natural language questions into SQL queries using Mistral AI for embeddings and chat models, with Neon PostgreSQL as the vector database.

## 🚀 Features

- **Natural Language to SQL**: Convert plain English questions to accurate SQL queries
- **RAG-based Context**: Retrieves relevant database schema and example queries for better accuracy
- **Production Ready**: Modular architecture with proper error handling and validation
- **Multiple Interfaces**: CLI tool, interactive mode, and Python API
- **Northwind Dataset**: Includes complete sample database with realistic business data

## 🏗️ Architecture

The system uses a RAG approach to improve SQL generation:

1. **Embeddings Storage**: Database schema (DDL) and example queries are embedded and stored in Neon PostgreSQL with pgvector
2. **Context Retrieval**: For each question, relevant schema information and similar query examples are retrieved
3. **SQL Generation**: Mistral AI chat model generates SQL using the retrieved context
4. **Validation & Execution**: Generated SQL is validated and optionally executed

## 📦 Installation

### Prerequisites

- Python 3.13+
- [UV](https://docs.astral.sh/uv/) package manager
- Mistral AI API key ([Get one here](https://console.mistral.ai/))
- Neon PostgreSQL database ([Create one here](https://console.neon.tech/))

### Setup

1. **Setup Infrastructure** (Optional but recommended):
   ```bash
   # Install Pulumi and Python dependencies for infrastructure
   cd infra
   uv sync
   
   # Deploy Neon database and get connection string
   pulumi up
   ```
   
   This will create a managed Neon PostgreSQL database for you. The connection string will be output after deployment.

2. **Clone and install dependencies**:
   ```bash
   git clone <repository-url>
   cd ragql
   uv sync
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys and database connection string
   # If you used Pulumi in step 1, use the connection string from the output
   ```

4. **Setup the system**:
   ```bash
   uv run python -m src.ragql.cli setup
   ```

## 🔧 Configuration

Required environment variables in `.env`:

```env
# Mistral AI API key from https://console.mistral.ai/
MISTRAL_API_KEY=your-mistral-api-key

# Neon connection string from https://console.neon.tech/
NEON_CONNECTION_STRING=postgresql://user:pass@host/db?sslmode=require
```

**Recommended for optimal performance:**

```env
# Hugging Face token for optimized embedding tokenization
# Get a free token at: https://huggingface.co/settings/tokens
# Without this, embeddings will use fallback tokenizer with reduced batch performance
HF_TOKEN=your-huggingface-token
```

Optional configuration:
- `COLLECTION_NAME`: Vector store collection name (default: `text-to-sql-context`)
- `EMBEDDING_MODEL`: Mistral embedding model (default: `mistral-embed`)
- `CHAT_MODEL`: Mistral chat model (default: `mistral-medium`)
- `MAX_SCHEMA_RESULTS`: Max DDL statements to retrieve (default: `5`)
- `MAX_QUERY_EXAMPLES`: Max example queries to retrieve (default: `3`)

### Performance Note

The system will work without `HF_TOKEN` but you may see warnings about tokenizer performance. For optimal embedding batch processing, especially with large datasets, it's recommended to:

1. Visit [Hugging Face Settings](https://huggingface.co/settings/tokens)
2. Create a free account and generate a "Read" access token
3. Add it to your `.env` file as `HF_TOKEN=your-token-here`

## 💻 Usage

### Command Line Interface

**Single Query**:
```bash
# Generate SQL only
uv run python -m src.ragql.cli query "Find all customers from France"

# Generate and execute SQL
uv run python -m src.ragql.cli query -e "Find top 5 products by sales"
```

**Interactive Mode**:
```bash
uv run python -m src.ragql.cli interactive
```

**Batch Processing**:
```bash
# Create questions.txt with one question per line
echo "Find all customers from France" > questions.txt
echo "Show top 5 products by sales" >> questions.txt

uv run python -m src.ragql.cli batch -i questions.txt -o results.json
```

**System Status**:
```bash
uv run python -m src.ragql.cli status
```

### Python API

```python
from src.ragql.config import Config
from src.ragql.database import DatabaseManager
from src.ragql.embeddings import EmbeddingsManager
from src.ragql.query import QueryGenerator

# Initialize components
config = Config.from_env()
db_manager = DatabaseManager(config)
embeddings_manager = EmbeddingsManager(config, db_manager)
query_generator = QueryGenerator(config, embeddings_manager)

# Generate and execute SQL
question = "Find employees who processed the most orders"
result = query_generator.generate_with_execution(question)

print(f"SQL: {result['sql']}")
print(f"Results: {result['results']}")
```

### Main Application

```bash
# Run the main application with sample query
uv run python main.py
```

## 🗄️ Database Schema

The system uses the Northwind sample database, which models a trading company with:

- **Customers**: Customer information and contact details
- **Orders**: Order records with dates and shipping information  
- **Products**: Product catalog with categories and pricing
- **Employees**: Employee records and organizational structure
- **Categories**: Product categorization
- **Suppliers**: Supplier information and contacts

## 🧠 How It Works

### 1. Setup Phase
- Downloads Northwind schema and sample queries
- Creates database tables using provided DDL
- Generates embeddings for schema statements and example queries
- Stores embeddings in Neon PostgreSQL with pgvector

### 2. Query Processing
- User provides natural language question
- System retrieves relevant DDL statements using similarity search
- System retrieves similar example queries for few-shot learning
- Constructs prompt with context and question
- Mistral AI generates SQL query with step-by-step reasoning

### 3. Validation & Execution
- Validates generated SQL for safety (prevents destructive operations)
- Optionally executes query against database
- Returns structured results with metadata

## 🔍 Example Queries

The system can handle various types of business questions:

- **Basic queries**: "Show all customers from France"
- **Aggregations**: "Find the top 5 best-selling products"
- **Joins**: "List orders with customer names and shipping details"
- **Complex analysis**: "Which employee processed the most orders this year?"
- **Date filtering**: "Show sales data for the last quarter"

## 🛡️ Security Features

- **SQL Injection Prevention**: Validates queries before execution
- **Read-only Operations**: Blocks destructive SQL operations (DROP, DELETE, UPDATE)
- **Environment Variables**: Secure credential management
- **Error Handling**: Comprehensive error handling and logging

## 📁 Project Structure

```
ragql/
├── src/ragql/               # Main package
│   ├── config.py           # Configuration management
│   ├── database.py         # Database operations
│   ├── embeddings.py       # Vector store management
│   ├── query.py            # SQL generation logic
│   └── cli.py              # Command-line interface
├── data/                   # Database files
│   ├── northwind-schema.sql
│   └── northwind-queries.jsonl
├── tests/                  # Test files
├── main.py                 # Main application entry
├── .env.example            # Environment template
└── pyproject.toml          # UV configuration
```

## 🧪 Development

### Running Tests
```bash
uv add --dev pytest
uv run pytest
```

### Code Formatting
```bash
uv add --dev black ruff
uv run black src/
uv run ruff check src/
```

### Type Checking
```bash
uv add --dev mypy
uv run mypy src/
```

## 📚 API Reference

### Config Class
- `Config.from_env()`: Load configuration from environment variables
- `config.validate()`: Validate configuration settings

### DatabaseManager Class
- `test_connection()`: Test database connectivity
- `setup_schema()`: Initialize database schema
- `execute_query(sql)`: Execute SQL and return results
- `validate_query(sql)`: Validate SQL safety

### EmbeddingsManager Class
- `setup_vector_store()`: Initialize and populate vector store
- `search_similar_ddl(query)`: Find relevant schema information
- `search_similar_queries(query)`: Find example queries
- `get_context_for_query(query)`: Get complete context for question

### QueryGenerator Class
- `generate_sql(question)`: Generate SQL from natural language
- `generate_and_validate_sql(question)`: Generate and validate SQL
- `generate_with_execution(question)`: Generate, validate, and execute SQL

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🙏 Acknowledgments

- [Mistral AI](https://mistral.ai/) for embeddings and chat models
- [Neon](https://neon.tech/) for serverless PostgreSQL with pgvector
- [LangChain](https://langchain.com/) for RAG framework components
- Original Jupyter notebook from [Neon's cookbook](https://github.com/neondatabase/mistral-neon-text-to-sql)