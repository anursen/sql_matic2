import sqlite3
import os
import sys
import time
import re
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool

# Add parent directory to path to ensure imports work correctly
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

# Determine whether we're imported or run directly
is_imported = __name__ != "__main__"

try:
    # Import proper models according to guidelines
    from backend.models.data_models import ExecuteSqliteQuery, ExecuteSqliteQueryResponse, SqliteQueryResult
    from backend.utils.logger import get_logger, info, debug, warning, error, exception
    from backend.config.config import config
    
    # Get module-specific logger following centralized logging guideline
    logger = get_logger("sqlite_query")
    
except ImportError as e:
    try:
        # Try alternative import paths
        sys.path.insert(0, os.path.dirname(parent_dir))  # Go up one more level
        from backend.models.data_models import ExecuteSqliteQuery, ExecuteSqliteQueryResponse, SqliteQueryResult
        from backend.utils.logger import get_logger, info, debug, warning, error, exception
        from backend.config.config import config
        
        # Get logger for alternative path
        logger = get_logger("sqlite_query")
        
    except ImportError:
        # Final fallback - define minimal versions of what we need
        import logging
        print(f"Warning: Could not import models, using simplified versions. Error: {e}")
        
        # Create basic logger for standalone execution
        console_logger = logging.getLogger("sqlite_query")
        if not console_logger.handlers:
            console_logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
            console_logger.addHandler(handler)
        logger = console_logger
        
        # Define minimal versions of required classes following the same models
        @tool
        class SqliteExecuteQuery:
            def __init__(self, db_path, query, params=None, max_rows=None):
                self.db_path = db_path
                self.query = query
                self.params = params or {}
                self.max_rows = max_rows
        
        class SqliteQueryResult(dict):
            def __init__(self, columns=None, rows=None, row_count=0, execution_time_ms=0, 
                         affected_rows=None, is_select=True, sql_executed=""):
                data = {
                    "columns": columns or [],
                    "rows": rows or [],
                    "row_count": row_count,
                    "execution_time_ms": execution_time_ms,
                    "affected_rows": affected_rows,
                    "is_select": is_select,
                    "sql_executed": sql_executed
                }
                self.update(data)
            
            def model_dump(self):
                return dict(self)
                
        class ExecuteSqliteQueryResponse(dict):
            def __init__(self, results=None, error=None, is_write_operation=False, execution_time_ms=0):
                data = {
                    "results": results or [],
                    "error": error,
                    "is_write_operation": is_write_operation,
                    "execution_time_ms": execution_time_ms
                }
                self.update(data)
            
            def model_dump(self):
                return dict(self)
        
        # Create mock config following same interface
        class MockConfig:
            def get(self, section, key, default=None):
                return default
            
            def get_section(self, section):
                return {}
                
        config = MockConfig()

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
def execute_sqlite_query(db_path: str, query: str, params: Optional[Dict[str, Any]] = None, max_rows: Optional[int] = None) -> Dict[str, Any]:
    """
    Executes a SQLite query on the specified database file and returns the results.
    Support for SELECT, INSERT, UPDATE, DELETE, and other SQL operations.
    
    Args:
        db_path: Path to the SQLite database file
        query: SQL query or statement to execute
        params: Optional parameters for parameterized queries
        max_rows: Maximum number of rows to return (for SELECTs)
    
    Returns:
        A dictionary containing the query results and execution information
    """
    # Start timing
    start_time = time.time()
    
    # Log query attempt using centralized logger
    logger.info(f"Executing SQLite query on database: {db_path}")
    logger.debug(f"Query: {query}")
    
    if not os.path.exists(db_path):
        error_msg = f"Database file not found: {db_path}"
        logger.error(error_msg)
        return ExecuteSqliteQueryResponse(error=error_msg).model_dump()
    
    # Get configuration values from centralized config
    timeout = config.get("query_db", "timeout", 30)
    max_rows_return = max_rows or config.get("query_db", "max_rows_return", 1000)
    enable_write = config.get("query_db", "enable_write", False)
    
    # Check if this is a write operation
    query_is_write = is_write_operation(query)
    
    # If write operations are disabled and this is a write operation, return an error
    if query_is_write and not enable_write:
        error_msg = "Write operations are disabled in the configuration"
        logger.warning(f"Blocked write operation: {error_msg}")
        return ExecuteSqliteQueryResponse(
            error=error_msg,
            is_write_operation=True
        ).model_dump()
    
    # Split into multiple queries if needed
    queries = parse_multiple_queries(query)
    
    # Prepare parameters
    params_list = []
    if params is not None:
        # If a single set of parameters is provided, use it for all queries
        for _ in queries:
            params_list.append(params)
    else:
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
    """Allow direct execution for testing SQLite queries"""
    import argparse
    import json
    
    def test_queries():
        """Run a series of test queries to verify functionality"""
        try:
            logger.info("Starting SQLite query tests")
            
            # Get database path from query_db section in config
            db_path = config.get("query_db", "path", "user_files/sakila.db")
            logger.info(f"Using database: {db_path}")
            
            # Series of test queries - from simple to more complex
            test_cases = [
                {
                    "name": "SQLite Version",
                    "query": "SELECT sqlite_version();"
                },
                {
                    "name": "List Tables",
                    "query": "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name LIMIT 5;"
                },
                {
                    "name": "Count Tables",
                    "query": "SELECT COUNT(*) as table_count FROM sqlite_master WHERE type='table';"
                },
                {
                    "name": "Multiple Queries",
                    "query": """
                    SELECT COUNT(*) as count FROM sqlite_master WHERE type='table';
                    SELECT COUNT(*) as count FROM sqlite_master WHERE type='index';
                    """
                },
                {
                    "name": "Schema Info",
                    "query": """
                    SELECT m.name as table_name, 
                           p.name as column_name,
                           p.type as data_type,
                           p.pk as is_primary_key
                    FROM sqlite_master m
                    JOIN pragma_table_info(m.name) p
                    WHERE m.type = 'table'
                    LIMIT 10;
                    """
                }
            ]
            
            # Run each test case
            for i, test in enumerate(test_cases, 1):
                logger.info(f"Test {i}: {test['name']}")
                logger.debug(f"Query: {test['query']}")
                
                # Create a proper input object for the tool 
                # This works with the latest LangChain tools
                tool_input = {
                    "db_path": db_path,
                    "query": test["query"]
                }
                
                # Execute the query using the tool's invoke method
                result = execute_sqlite_query.invoke(tool_input)
                
                # Check for errors
                if result.get("error"):
                    logger.error(f"Query failed: {result['error']}")
                else:
                    # Extract and display results
                    logger.info(f"Query succeeded in {result['execution_time_ms']}ms")
                    
                    for j, query_result in enumerate(result.get("results", []), 1):
                        if query_result.get("is_select", True):
                            columns = query_result.get("columns", [])
                            rows = query_result.get("rows", [])
                            logger.info(f"Result set {j}: {len(rows)} rows, columns: {', '.join(columns)}")
                            
                            # Print limited results for visual inspection
                            if rows and len(rows) > 0:
                                print("\nResults preview:")
                                # Format as table with column headers
                                print(" | ".join([str(col).ljust(15) for col in columns]))
                                print("-" * (20 * len(columns)))
                                
                                # Print up to 5 rows
                                for row_idx, row in enumerate(rows[:5]):
                                    print(" | ".join([str(cell).ljust(15) for cell in row]))
                                
                                if len(rows) > 5:
                                    print(f"... and {len(rows) - 5} more rows")
                        else:
                            affected = query_result.get("affected_rows", 0)
                            logger.info(f"Result set {j}: Non-SELECT query, affected rows: {affected}")
                
                print("\n" + "="*50 + "\n")
            
            logger.info("All tests completed")
            
        except Exception as e:
            logger.exception(f"Error during test execution: {str(e)}")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Execute SQLite queries")
    parser.add_argument("--db", help="Path to SQLite database")
    parser.add_argument("--query", help="SQL query to execute")
    parser.add_argument("--params", help="JSON string of parameters")
    parser.add_argument("--max-rows", type=int, help="Maximum rows to return")
    parser.add_argument("--test", action="store_true", help="Run predefined test queries")
    
    args = parser.parse_args()
    
    # If --test flag is provided, run test queries
    if args.test:
        test_queries()
    # Otherwise execute a specific query from command line args
    elif args.query:
        params = None
        if args.params:
            try:
                params = json.loads(args.params)
            except json.JSONDecodeError:
                logger.error(f"Error: Could not parse parameters JSON: {args.params}")
                sys.exit(1)
        
        # Get db_path from command line or from query_db section in config
        db_path = args.db or config.get("query_db", "path", "user_files/sakila.db")
        
        # Create proper input for the tool
        tool_input = {
            "db_path": db_path,
            "query": args.query
        }
        
        # Add optional parameters if provided
        if params:
            tool_input["params"] = params
        if args.max_rows:
            tool_input["max_rows"] = args.max_rows
        
        # Use the invoke method instead of calling directly
        result = execute_sqlite_query.invoke(tool_input)
        
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()
        print("\nTip: Use --test to run predefined test queries")

