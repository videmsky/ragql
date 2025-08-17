"""Command-line interface for RAG-QL text-to-SQL system."""

import click
import logging
import sys
import json
import warnings
from typing import Optional

# Suppress the Hugging Face tokenizer warning for cleaner CLI output
# The actual tokenizer status will be logged informatively by the embeddings manager
warnings.filterwarnings("ignore", message="Could not download mistral tokenizer from Huggingface*")

from .config import Config
from .database import DatabaseManager
from .embeddings import EmbeddingsManager
from .query import QueryGenerator

logger = logging.getLogger(__name__)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """RAG-QL: Convert natural language to SQL using Mistral AI and Neon PostgreSQL."""
    ctx.ensure_object(dict)
    
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        config = Config.from_env()
        config.validate()
        ctx.obj['config'] = config
    except Exception as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def setup(ctx):
    """Setup the database schema and initialize vector store."""
    config = ctx.obj['config']
    
    try:
        click.echo("Setting up RAG-QL system...")
        
        db_manager = DatabaseManager(config)
        if not db_manager.test_connection():
            click.echo("Database connection failed!", err=True)
            sys.exit(1)
        
        click.echo("✓ Database connection successful")
        
        click.echo("Setting up database schema...")
        db_manager.setup_schema()
        click.echo("✓ Database schema setup completed")
        
        click.echo("Initializing embeddings...")
        embeddings_manager = EmbeddingsManager(config, db_manager)
        embeddings_manager.setup_vector_store()
        click.echo("✓ Vector store setup completed")
        
        stats = embeddings_manager.get_collection_stats()
        click.echo(f"✓ Embedded {stats['ddl_count']} DDL statements and {stats['query_count']} sample queries")
        
        click.echo("🎉 RAG-QL system setup completed successfully!")
        
    except Exception as e:
        click.echo(f"Setup failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('question')
@click.option('--execute', '-e', is_flag=True, help='Execute the generated SQL query')
@click.option('--validate', is_flag=True, default=True, help='Validate the generated SQL')
@click.option('--format', 'output_format', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def query(ctx, question, execute, validate, output_format):
    """Generate SQL from natural language question."""
    config = ctx.obj['config']
    
    try:
        db_manager = DatabaseManager(config)
        embeddings_manager = EmbeddingsManager(config, db_manager)
        query_generator = QueryGenerator(config, embeddings_manager)
        
        if execute:
            result = query_generator.generate_with_execution(question)
        else:
            result = query_generator.generate_and_validate_sql(question, validate)
        
        if output_format == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            _print_query_result(result, execute)
    
    except Exception as e:
        click.echo(f"Query generation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--input-file', '-i', type=click.File('r'), help='Input file with questions (one per line)')
@click.option('--output-file', '-o', type=click.File('w'), help='Output file for results')
@click.option('--execute', '-e', is_flag=True, help='Execute the generated SQL queries')
@click.pass_context
def batch(ctx, input_file, output_file, execute):
    """Process multiple questions in batch mode."""
    config = ctx.obj['config']
    
    if not input_file:
        click.echo("Please provide an input file with --input-file", err=True)
        sys.exit(1)
    
    try:
        questions = [line.strip() for line in input_file if line.strip()]
        click.echo(f"Processing {len(questions)} questions...")
        
        db_manager = DatabaseManager(config)
        embeddings_manager = EmbeddingsManager(config, db_manager)
        query_generator = QueryGenerator(config, embeddings_manager)
        
        results = []
        for i, question in enumerate(questions, 1):
            click.echo(f"Processing {i}/{len(questions)}: {question[:50]}...")
            
            if execute:
                result = query_generator.generate_with_execution(question)
            else:
                result = query_generator.generate_sql(question)
            
            results.append(result)
        
        if output_file:
            json.dump(results, output_file, indent=2)
            click.echo(f"Results saved to {output_file.name}")
        else:
            for result in results:
                _print_query_result(result, execute)
                click.echo("-" * 60)
    
    except Exception as e:
        click.echo(f"Batch processing failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive mode for querying."""
    config = ctx.obj['config']
    
    try:
        click.echo("🚀 Starting RAG-QL Interactive Mode")
        click.echo("Type your questions in natural language. Type 'quit' to exit.\n")
        
        db_manager = DatabaseManager(config)
        embeddings_manager = EmbeddingsManager(config, db_manager)
        query_generator = QueryGenerator(config, embeddings_manager)
        
        while True:
            question = click.prompt("Question", type=str)
            
            if question.lower() in ('quit', 'exit', 'q'):
                click.echo("Goodbye! 👋")
                break
            
            try:
                result = query_generator.generate_with_execution(question)
                _print_query_result(result, True)
            except Exception as e:
                click.echo(f"Error: {e}", err=True)
            
            click.echo()
    
    except KeyboardInterrupt:
        click.echo("\nGoodbye! 👋")
    except Exception as e:
        click.echo(f"Interactive mode failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status and statistics."""
    config = ctx.obj['config']
    
    try:
        db_manager = DatabaseManager(config)
        
        click.echo("RAG-QL System Status")
        click.echo("=" * 30)
        
        # Test database connection
        if db_manager.test_connection():
            click.echo("✓ Database: Connected")
        else:
            click.echo("✗ Database: Connection failed")
            return
        
        # Get embeddings stats
        embeddings_manager = EmbeddingsManager(config, db_manager)
        stats = embeddings_manager.get_collection_stats()
        
        click.echo(f"✓ Vector Store: {stats['total_count']} documents")
        click.echo(f"  - DDL Statements: {stats['ddl_count']}")
        click.echo(f"  - Query Examples: {stats['query_count']}")
        
        # Test table info
        table_info = db_manager.get_table_info()
        if table_info:
            tables = set(row['table_name'] for row in table_info)
            click.echo(f"✓ Database Tables: {len(tables)} tables available")
        
        click.echo("\nConfiguration:")
        click.echo(f"  - Embedding Model: {config.embedding_model}")
        click.echo(f"  - Chat Model: {config.chat_model}")
        click.echo(f"  - Collection: {config.collection_name}")
    
    except Exception as e:
        click.echo(f"Status check failed: {e}", err=True)
        sys.exit(1)


def _print_query_result(result, show_results=False):
    """Print query result in a formatted way."""
    click.echo(f"Question: {result['question']}")
    
    if result.get('error'):
        click.echo(f"❌ Error: {result['error']}", err=True)
        return
    
    if result.get('sql'):
        click.echo(f"Generated SQL:")
        click.echo(f"  {result['sql']}")
        
        if result.get('is_valid') is False:
            click.echo("⚠️  SQL validation failed", err=True)
    
    if show_results and result.get('results'):
        click.echo(f"Results ({result['row_count']} rows):")
        for i, row in enumerate(result['results'][:10], 1):  # Show first 10 rows
            click.echo(f"  {i}: {row}")
        
        if result['row_count'] > 10:
            click.echo(f"  ... ({result['row_count'] - 10} more rows)")
    
    elif show_results and result.get('execution_error'):
        click.echo(f"❌ Execution error: {result['execution_error']}", err=True)


def main():
    """Main CLI entry point."""
    cli()


if __name__ == '__main__':
    main()