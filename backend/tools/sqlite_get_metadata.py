import sqlite3
import os
import sys
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
from datetime import datetime
from pathlib import Path

# Add parent directory to path to ensure imports work correctly
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

from models.data_models import SqliteGetMetadataArgs, SQLiteGetMetadataResponse, DatabaseStats

# Determine whether we're imported or run directly
is_imported = __name__ != "__main__"

# Import configuration and logging

from config.config import config
from utils.logger import get_logger

tools_logger = get_logger("tools")

@tool(args_schema=SqliteGetMetadataArgs)
def sqlite_get_metadata(table_count: int) -> Dict[str, Any]:
    """
    Returns metadata about a SQLite database including table sizes, row counts,
    and other statistics without duplicating schema information.
    
    Args:
        table_count (int): Maximum number of tables to return metadata for (0 for all tables)
    Returns:
        A dictionary containing statistics and metadata about the database
    """
    # Get database path from configuration
    
    db_path =  config.get("query_db", "path")
    error_msg = f"Extracting metadata from SQLite database: {db_path}"
    tools_logger.info(error_msg)
    
    if not os.path.exists(db_path):
        tools_logger.error(f"Database file not found: {db_path}")
        return SQLiteGetMetadataResponse(
            database_info={},
            table_stats=[],
            stats=DatabaseStats(),
            error=error_msg
        ).model_dump()
    
    conn = None
    try:
        # Database file information
        db_size = os.path.getsize(db_path)
        database_name = os.path.basename(db_path)
        creation_time = datetime.fromtimestamp(os.path.getctime(db_path)).isoformat()
        modification_time = datetime.fromtimestamp(os.path.getmtime(db_path)).isoformat()
        
        # Get config values
        timeout = config.get("query_db", "timeout", 30)
        excluded_tables = config.get("query_db", "excluded_tables", [])
        sample_rows = config.get("query_db", "sample_rows", 5)
        
        # Connect to the database with configured timeout
        conn = sqlite3.connect(db_path, timeout=timeout)
        cursor = conn.cursor()
        
        # Get database page information
        cursor.execute("PRAGMA page_size;")
        page_size = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA page_count;")
        page_count = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA encoding;")
        encoding = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA auto_vacuum;")
        auto_vacuum = cursor.fetchone()[0]
        
        # Collect database-level information
        database_info = {
            "name": database_name,
            "path": db_path,
            "size_bytes": db_size,
            "size_human": f"{db_size / (1024 * 1024):.2f} MB" if db_size > 1024 * 1024 else f"{db_size / 1024:.2f} KB",
            "page_size": page_size,
            "page_count": page_count,
            "encoding": encoding,
            "journal_mode": journal_mode,
            "auto_vacuum": auto_vacuum,
            "creation_time": creation_time,
            "modification_time": modification_time
        }
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        # Filter out excluded tables
        all_table_names = [name for name in all_tables if name not in excluded_tables]
        all_table_count = len(all_table_names)
        
        # Apply table_count limit if specified
        if table_count > 0 and table_count < all_table_count:
            table_names = all_table_names[:table_count]
        else:
            table_names = all_table_names
            table_count = all_table_count
        
        tools_logger.debug(f"Found {all_table_count} tables (excluded {len(all_tables) - all_table_count}), returning {len(table_names)}")
        
        table_stats = []
        total_rows = 0
        total_size_estimate = 0
        
        # Maximum number of rows to analyze per table (from config)
        max_rows_return = config.get("query_db", "max_rows_return", 1000)
        
        # Gather statistics for each table
        for table_name in table_names:
            try:
                # Get row count
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM '{table_name}';")
                    row_count = cursor.fetchone()[0]
                    total_rows += row_count
                except sqlite3.Error as e:
                    tools_logger.warning(f"Error counting rows in table '{table_name}': {str(e)}")
                    row_count = 0
                
                # Get column count
                cursor.execute(f"PRAGMA table_info('{table_name}');")
                columns_data = cursor.fetchall()
                column_count = len(columns_data)
                
                # Estimate table size by sampling rows
                avg_row_size = 0
                if row_count > 0:
                    try:
                        # Sample multiple rows to get better size estimate
                        sample_limit = min(sample_rows, row_count)
                        cursor.execute(f"SELECT * FROM '{table_name}' LIMIT {sample_limit};")
                        sample_rows_data = cursor.fetchall()
                        
                        if sample_rows_data:
                            # Calculate average row size from samples
                            total_sample_size = sum(
                                sum(len(str(cell)) for cell in row if cell is not None)
                                for row in sample_rows_data
                            )
                            avg_row_size = total_sample_size / len(sample_rows_data)
                    except sqlite3.Error as e:
                        tools_logger.warning(f"Error sampling rows from table '{table_name}': {str(e)}")
                
                estimated_size = avg_row_size * row_count
                total_size_estimate += estimated_size
                
                # Get index information
                cursor.execute(f"PRAGMA index_list('{table_name}');")
                indices = cursor.fetchall()
                index_count = len(indices)
                
                # Create table statistics
                table_stats.append({
                    "name": table_name,
                    "row_count": row_count,
                    "column_count": column_count,
                    "index_count": index_count,
                    "avg_row_size_bytes": avg_row_size,
                    "estimated_size_bytes": int(estimated_size),  # Convert to integer
                    "estimated_size_human": f"{estimated_size / (1024 * 1024):.2f} MB" if estimated_size > 1024 * 1024 else f"{estimated_size / 1024:.2f} KB"
                })
                
            except sqlite3.Error as e:
                tools_logger.error(f"Error analyzing table '{table_name}': {str(e)}")
                # Add basic entry for the table with error info
                table_stats.append({
                    "name": table_name,
                    "row_count": 0,
                    "column_count": 0,
                    "index_count": 0,
                    "avg_row_size_bytes": 0,
                    "estimated_size_bytes": 0,
                    "estimated_size_human": "0 KB",
                    "error": str(e)
                })
        
        # Create DatabaseStats object
        stats = DatabaseStats(
            databaseCount=1,
            tableCount=len(table_names),
            rowCount=total_rows
        )
        
        tools_logger.info(f"Successfully extracted metadata from {db_path}: {len(table_stats)} tables, {total_rows} total rows")
        
        # Add informational message about table count
        database_info["message"] = f"Returning response for {table_count}/{all_table_count} tables"
        
        # Return response
        return SQLiteGetMetadataResponse(
            database_info=database_info,
            table_stats=table_stats,
            stats=stats
        ).model_dump()
        
    except sqlite3.Error as e:
        error_msg = f"SQLite error: {str(e)}"
        tools_logger.error(f"Failed to extract metadata from {db_path}: {error_msg}")
        # Create minimal valid database_info with required fields
        return SQLiteGetMetadataResponse(
            database_info={
                "name": os.path.basename(db_path) if db_path else "unknown",
                "path": db_path if db_path else "unknown",
                "size_bytes": 0
            },
            table_stats=[],
            stats=DatabaseStats(),
            error=error_msg
        ).model_dump()
    except Exception as e:
        # Catch any other exceptions to prevent app failure
        error_msg = f"Unexpected error: {str(e)}"
        tools_logger.exception(f"Unexpected error extracting metadata from {db_path}")
        # Create minimal valid database_info with required fields
        return SQLiteGetMetadataResponse(
            database_info={
                "name": os.path.basename(db_path) if db_path else "unknown",
                "path": db_path if db_path else "unknown",
                "size_bytes": 0
            },
            table_stats=[],
            stats=DatabaseStats(),
            error=error_msg
        ).model_dump()
    finally:
        if conn:
            conn.close()

def main():

    result = sqlite_get_metadata.invoke({"table_count": 0})
    import pprint
    pprint.pprint(result)
if __name__ == "__main__":
    main()

