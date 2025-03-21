import sqlite3
import os
import sys
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from datetime import datetime
# Add parent directory to path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Try different import paths depending on context
try:
    # This will work when imported from main.py
    from models.data_models import GetSqliteMetadata, DatabaseStats
except ImportError:
    try:
        # This will work when run directly or from certain contexts
        from backend.models.data_models import GetSqliteMetadata, DatabaseStats
    except ImportError:
        # Final fallback
        from data_models import GetSqliteMetadata, DatabaseStats

class SQLiteMetadataResponse(BaseModel):
    """Response model for SQLite metadata"""
    database_info: Dict[str, Any]
    table_stats: List[Dict[str, Any]]
    stats: DatabaseStats
    error: Optional[str] = None

# Suppress urllib3 warnings
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)
except (ImportError, AttributeError):
    pass

@tool(args_schema=GetSqliteMetadata)
def get_sqlite_metadata(db_path: str) -> Dict[str, Any]:
    """
    Returns metadata about a SQLite database including table sizes, row counts,
    and other statistics without duplicating schema information.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        A dictionary containing statistics and metadata about the database
    """
    if not os.path.exists(db_path):
        return SQLiteMetadataResponse(
            database_info={},
            table_stats=[],
            stats=DatabaseStats(),
            error=f"Database file not found: {db_path}"
        ).model_dump()
    
    conn = None
    try:
        # Database file information
        db_size = os.path.getsize(db_path)
        database_name = os.path.basename(db_path)
        creation_time = datetime.fromtimestamp(os.path.getctime(db_path)).isoformat()
        modification_time = datetime.fromtimestamp(os.path.getmtime(db_path)).isoformat()
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
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
        table_names = [row[0] for row in cursor.fetchall()]
        
        table_stats = []
        total_rows = 0
        total_size_estimate = 0
        
        # Gather statistics for each table
        for table_name in table_names:
            # Get row count
            try:
                cursor.execute(f"SELECT COUNT(*) FROM '{table_name}';")
                row_count = cursor.fetchone()[0]
                total_rows += row_count
            except sqlite3.Error:
                row_count = 0
            
            # Get column count
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            columns_data = cursor.fetchall()
            column_count = len(columns_data)
            
            # Estimate table size
            avg_row_size = 0
            if row_count > 0:
                try:
                    cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 1;")
                    sample_row = cursor.fetchone()
                    if sample_row:
                        # Rough estimation of row size in bytes
                        avg_row_size = sum(len(str(cell)) for cell in sample_row if cell is not None)
                except sqlite3.Error:
                    pass
            
            estimated_size = avg_row_size * row_count
            total_size_estimate += estimated_size
            
            # Get index information
            cursor.execute(f"PRAGMA index_list('{table_name}');")
            indices = cursor.fetchall()
            index_count = len(indices)
            
            # Get last modified time (from SQLITE_MASTER)
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            
            # Create table statistics
            table_stats.append({
                "name": table_name,
                "row_count": row_count,
                "column_count": column_count,
                "index_count": index_count,
                "avg_row_size_bytes": avg_row_size,
                "estimated_size_bytes": estimated_size,
                "estimated_size_human": f"{estimated_size / (1024 * 1024):.2f} MB" if estimated_size > 1024 * 1024 else f"{estimated_size / 1024:.2f} KB"
            })
        
        # Create DatabaseStats object
        stats = DatabaseStats(
            databaseCount=1,
            tableCount=len(table_names),
            rowCount=total_rows
        )
        
        # Return response
        return SQLiteMetadataResponse(
            database_info=database_info,
            table_stats=table_stats,
            stats=stats
        ).model_dump()
        
    except sqlite3.Error as e:
        return SQLiteMetadataResponse(
            database_info={},
            table_stats=[],
            stats=DatabaseStats(),
            error=f"SQLite error: {str(e)}"
        ).model_dump()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Example usage

    db_path = '../user_files/sakila.db'

    #result = get_sqlite_metadata.invoke(db_path)
    #print(result)
    #print(result.get('database_info'))
    #print(result.get('table_stats'))
    #table_stats: List[TableStats] = []
    #print(result.get('stats'))
    #stats: DatabaseStats
    #print(result.get('error'))
    #error')
