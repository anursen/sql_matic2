import sqlite3
import os
import sys
import time
import re
from langchain_core.tools import tool
from typing import List, Optional


# Determine whether we're imported or run directly
is_imported = __name__ != "__main__"
# Add parent directory to path to ensure imports work correctly
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

from models.data_models import ExecuteSqliteQuery,ExecuteSqliteQueryResponse, SqliteQueryResult

# Determine whether we're imported or run directly
is_imported = __name__ != "__main__"

# Import configuration and logging

from config.config import config
from utils.logger import logger
logger.info("Initializing SQLite query execution tool")

# Helper functions
def is_write_operation(query: str) -> bool:
    """
    Determine if a SQL query is a write operation.
    
    Args:
        query: SQL query string
        
    Returns:
        bool: True if the query is a write operation, False otherwise
    """
    # Remove comments and standardize whitespace
    clean_query = re.sub(r'--.*?(\n|$)', ' ', query)
    clean_query = re.sub(r'/\*.*?\*/', ' ', clean_query, flags=re.DOTALL)
    clean_query = clean_query.strip().upper()
    
    # Check if the query starts with a write operation keyword
    write_operations = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'REPLACE']
    
    for op in write_operations:
        if clean_query.startswith(op):
            return True
    
    return False

def parse_multiple_queries(query_str: str) -> List[str]:
    """
    Split a string containing multiple SQL queries into individual queries.
    Handles basic SQL syntax including semicolons inside quotes and comments.
    
    Args:
        query_str: String containing one or more SQL queries
        
    Returns:
        List of individual SQL queries
    """
    # Simple but effective for most cases
    queries = []
    current_query = ""
    in_single_quote = False
    in_double_quote = False
    i = 0
    
    while i < len(query_str):
        char = query_str[i]
        
        # Handle quotes
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        
        # Handle comments
        if char == '-' and i + 1 < len(query_str) and query_str[i+1] == '-' and not in_single_quote and not in_double_quote:
            # Skip to end of line
            current_query += char
            i += 1
            while i < len(query_str) and query_str[i] != '\n':
                current_query += query_str[i]
                i += 1
            if i < len(query_str):
                current_query += query_str[i]  # Add the newline
        elif char == '/' and i + 1 < len(query_str) and query_str[i+1] == '*' and not in_single_quote and not in_double_quote:
            # Skip multi-line comment
            current_query += char
            i += 1
            while i + 1 < len(query_str) and not (query_str[i] == '*' and query_str[i+1] == '/'):
                current_query += query_str[i]
                i += 1
            if i + 1 < len(query_str):
                current_query += "*/"
                i += 1
        
        # Handle semicolons outside of quotes
        elif char == ';' and not in_single_quote and not in_double_quote:
            current_query += char
            trimmed_query = current_query.strip()
            if trimmed_query:  # Avoid adding empty queries
                queries.append(trimmed_query)
            current_query = ""
        else:
            current_query += char
        
        i += 1
    
    # Add the last query if it's not empty
    trimmed_query = current_query.strip()
    if trimmed_query:
        queries.append(trimmed_query)
    
    return queries

@tool(args_schema=ExecuteSqliteQuery)
def execute_sqlite_query(query: str, ):
    """
    Executes a SQLite query on the specified database file or the configured default and returns the results.
    Support for SELECT, INSERT, UPDATE, DELETE, and other SQL operations.
    
    Args:
        query: SQL query or statement to execute
        db_path: Optional path to a specific SQLite database file (uses configured default if not provided)
    
    Returns:
        A dictionary containing the query results and execution information
    """
    # Start timing
    start_time = time.time()
    
    db_path = config.get("query_db", "path")
    
    # Log query attempt using centralized logger
    logger.info(f"Executing SQLite query on database: {db_path}")
    logger.debug(f"Query: {query}")
    
    # Get configuration values from centralized config
    timeout = config.get("query_db", "timeout", 30)
    max_rows_return = config.get("query_db", "max_rows_return", 1000)
    enable_write = config.get("query_db", "enable_write", False)
    
    # Check if this is a write operation
    query_is_write = is_write_operation(query)
    
    # If write operations are disabled and this is a write operation, return an error
    if query_is_write and not enable_write:
        error_msg = "Write operations are disabled in the configuration"
        logger.warning(f"Blocked write operation: {error_msg}")
        return ExecuteSqliteQueryResponse(
            error=error_msg,
            is_write_operation=query_is_write,
            results=[]
        ).model_dump()
    
    # Split into multiple queries if needed
    queries = parse_multiple_queries(query)
    
    # Prepare parameters
    params_list = [None] * len(queries)
    
    conn = None
    results = []
    total_execution_time = 0
    
    try:
        # Connect to database with configured timeout
        conn = sqlite3.connect(db_path, timeout=timeout)
        
        # Set row factory to return rows as lists instead of tuples (easier to serialize)
        conn.row_factory = lambda cursor, row: list(row)
        
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON;")
        
        # Execute each query
        for i, (query_str, query_params) in enumerate(zip(queries, params_list)):
            # Skip empty queries
            if not query_str.strip():
                continue
                
            query_start_time = time.time()
            cursor = conn.cursor()
            
            try:
                # Execute the query
                logger.debug(f"Executing query {i+1}/{len(queries)}: {query_str}")
                cursor.execute(query_str, query_params or {})
                
                # For SELECT statements, fetch results
                is_select = query_str.strip().upper().startswith("SELECT") or "SELECT" in query_str.strip().upper()
                
                if is_select:
                    # Get column names
                    columns = [col[0] for col in cursor.description] if cursor.description else []
                    
                    # Get rows (limit to max_rows_return)
                    rows = cursor.fetchmany(max_rows_return)
                    row_count = len(rows)
                    
                    # Check if there might be more rows
                    more_rows_exist = False
                    if row_count == max_rows_return:
                        # Try to fetch one more row to see if there are more
                        more_row = cursor.fetchone()
                        if more_row:
                            more_rows_exist = True
                            logger.info(f"Query returned more rows than the limit ({max_rows_return})")
                    
                    result = SqliteQueryResult(
                        columns=columns,
                        rows=rows,
                        row_count=row_count,
                        execution_time_ms=int((time.time() - query_start_time) * 1000),
                        is_select=True,
                        sql_executed=query_str
                    )
                    
                else:
                    # For non-SELECT, return affected row count
                    result = SqliteQueryResult(
                        columns=[],
                        rows=[],
                        row_count=0,
                        affected_rows=cursor.rowcount,
                        execution_time_ms=int((time.time() - query_start_time) * 1000),
                        is_select=False,
                        sql_executed=query_str
                    )
                
                results.append(result.model_dump())
                
                # If this was a write operation and we're not in a transaction, commit
                if query_is_write and not conn.in_transaction:
                    conn.commit()
                
                # Add to total execution time
                total_execution_time += (time.time() - query_start_time)
                
            except sqlite3.Error as e:
                # Roll back any changes from this query
                conn.rollback()
                error_msg = f"SQLite error (query {i+1}): {str(e)}"
                logger.error(error_msg)
                return ExecuteSqliteQueryResponse(
                    error=error_msg,
                    is_write_operation=query_is_write,
                    results=results  # Return any successful results so far
                ).model_dump()
        
        # Commit at the end if there are any pending transactions
        if query_is_write and conn.in_transaction:
            conn.commit()
        
        # Calculate total execution time
        total_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Successfully executed {len(results)} queries in {total_time_ms}ms")
        
        # Return response
        return ExecuteSqliteQueryResponse(
            results=results,
            is_write_operation=query_is_write,
            execution_time_ms=total_time_ms
        ).model_dump()
        
    except sqlite3.Error as e:
        if conn and conn.in_transaction:
            conn.rollback()
        
        error_msg = f"SQLite error: {str(e)}"
        logger.error(f"Failed to execute query: {error_msg}")
        return ExecuteSqliteQueryResponse(
            error=error_msg,
            is_write_operation=query_is_write,
            results=results  # Return any successful results
        ).model_dump()
    except Exception as e:
        if conn and conn.in_transaction:
            conn.rollback()
            
        # Catch any other exceptions to prevent app failure
        error_msg = f"Unexpected error: {str(e)}"
        logger.exception(f"Unexpected error executing query on {db_path}")
        return ExecuteSqliteQueryResponse(
            error=error_msg,
            is_write_operation=query_is_write,
            results=results  # Return any successful results
        ).model_dump()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    def test_sqlite_query_execution():
        print("SQLite Query Execution Tester")
        while True:
            query = input("> ")
            if query.lower().strip() in ('exit', 'quit', 'q'):
                print("Exiting tester.")
                break
                
            
            result = execute_sqlite_query.invoke({'query': query})
            print(result)
    
    # Run the tester
    test_sqlite_query_execution()