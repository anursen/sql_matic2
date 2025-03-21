import sqlite3
import os
import sys
import logging
from typing import Dict, List, Any
from langchain_core.tools import tool

# Configure a standalone logger for direct execution
def setup_standalone_logger():
    logger = logging.getLogger("sqlite_schema")
    if not logger.handlers:  # Only add handler if not already configured
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
    return logger

# Add parent directory to path to ensure imports work correctly
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

# Determine whether we're imported or run directly
is_imported = __name__ != "__main__"

try:
    # First try importing relative to backend root
    if is_imported:
        from models.data_models import Column, Table, Database, DatabaseStructure, GetSqliteMetadata, GetSqliteSchemaResponse
        from backend.utils import logger
    else:
        from backend.models.data_models import Column, Table, Database, DatabaseStructure, GetSqliteMetadata, GetSqliteSchemaResponse
        # When run directly, use standalone logger
        logger = setup_standalone_logger()
except ImportError as e:
    try:
        # Try alternative import paths
        sys.path.insert(0, os.path.dirname(parent_dir))  # Go up one more level
        from backend.models.data_models import Column, Table, Database, DatabaseStructure, GetSqliteMetadata, GetSqliteSchemaResponse
        from backend.utils import logger
    except ImportError:
        # Final fallback - define minimal versions of what we need
        print(f"Warning: Could not import models, using simplified versions. Error: {e}")
        
        # Define minimal versions of required classes
        class Column(dict):
            def __init__(self, name, type, primary_key=False, foreign_key=False, references=None):
                self.update({"name": name, "type": type, "primary_key": primary_key, 
                             "foreign_key": foreign_key, "references": references})
            
            def model_dump(self):
                return dict(self)
                
        class Table(dict):
            def __init__(self, name, columns):
                self.update({"name": name, "columns": columns})
            
            def model_dump(self):
                return dict(self)
                
        class Database(dict):
            def __init__(self, name, tables):
                self.update({"name": name, "tables": tables})
            
            def model_dump(self):
                return dict(self)
                
        class DatabaseStructure(dict):
            def __init__(self, databases):
                self.update({"databases": databases})
            
            def model_dump(self):
                return dict(self)
                
        class GetSqliteMetadata(dict):
            db_path: str
            
        class GetSqliteSchemaResponse(dict):
            def __init__(self, database_schema=None, tables=None, error=None):
                data = {}
                if database_schema is not None:
                    data["database_schema"] = database_schema
                if tables is not None:
                    data["tables"] = tables
                if error is not None:
                    data["error"] = error
                self.update(data)
            
            def model_dump(self):
                return dict(self)
        
        # Create standalone logger
        logger = setup_standalone_logger()

# Add a try-except block to handle urllib3 warning
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)
except (ImportError, AttributeError):
    pass

@tool(args_schema=GetSqliteMetadata)
def get_sqlite_schema(db_path: str) -> Dict[str, Any]:
    """
    Extracts the complete schema information from a SQLite database.
    args:
        db_path: Path to the SQLite database file
    returns:
        A dictionary containing the database schema information
    """
    logger.info(f"Extracting schema from SQLite database: {db_path}")
    
    if not os.path.exists(db_path):
        error_msg = f"Database file not found: {db_path}"
        logger.error(error_msg)
        return GetSqliteSchemaResponse(error=error_msg).model_dump()
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query to get all database objects
        cursor.execute("""
            SELECT type, name FROM sqlite_master 
            WHERE type IN ('table', 'view')
            ORDER BY type, name;
        """)
        
        all_objects = cursor.fetchall()
        database_name = os.path.basename(db_path)
        tables = []
        table_names = []
        
        # Create dictionary to track all foreign keys
        fk_map = {}
        
        # First pass: collect all foreign keys
        for obj_type, obj_name in all_objects:
            if obj_type == 'table':
                try:
                    cursor.execute(f"PRAGMA foreign_key_list('{obj_name}');")
                    fks = cursor.fetchall()
                    
                    for fk in fks:
                        from_col = fk[3]  # local column
                        to_table = fk[2]  # referenced table
                        to_col = fk[4]    # referenced column
                        
                        # Store in format: {table.column: referenced_table.referenced_column}
                        fk_map[f"{obj_name}.{from_col}"] = f"{to_table}.{to_col}"
                except sqlite3.Error as e:
                    # Just log and continue if we can't get foreign keys
                    logger.warning(f"Could not retrieve foreign keys for table '{obj_name}': {str(e)}")
        
        # Second pass: build schema
        for obj_type, obj_name in all_objects:
            if obj_type == 'table' or obj_type == 'view':
                table_names.append(obj_name)
                
                # Get column information
                try:
                    cursor.execute(f"PRAGMA table_info('{obj_name}');")
                    columns_data = cursor.fetchall()
                    
                    columns = []
                    
                    for col in columns_data:
                        col_id, name, data_type, notnull, default_val, is_pk = col
                        
                        # Check if this column is a foreign key
                        fk_key = f"{obj_name}.{name}"
                        is_fk = fk_key in fk_map
                        fk_reference = None
                        
                        if is_fk:
                            ref = fk_map[fk_key].split(".")
                            fk_reference = {
                                "table": ref[0],
                                "column": ref[1]
                            }
                        
                        # Create Column object with simplified information
                        column = Column(
                            name=name,
                            type=data_type,
                            primary_key=bool(is_pk),
                            foreign_key=is_fk,
                            references=fk_reference
                        )
                        
                        columns.append(column)
                    
                    # Create Table object with columns
                    table = Table(
                        name=obj_name,
                        columns=columns
                    )
                    
                    tables.append(table.model_dump())
                except sqlite3.Error as e:
                    # Log error and continue with next table
                    logger.error(f"Error processing table '{obj_name}': {str(e)}")
                    continue
        
        # Create Database with tables
        database = Database(
            name=database_name,
            tables=tables
        )
        
        # Create DatabaseStructure
        db_structure = DatabaseStructure(databases=[database.model_dump()])
        
        logger.info(f"Successfully extracted schema from {db_path}: {len(tables)} tables found")
        
        # Return response
        return GetSqliteSchemaResponse(
            database_schema=db_structure.model_dump(),
            tables=table_names
        ).model_dump()
        
    except sqlite3.Error as e:
        error_msg = f"SQLite error: {str(e)}"
        logger.error(f"Failed to extract schema from {db_path}: {error_msg}")
        return GetSqliteSchemaResponse(error=error_msg).model_dump()
    except Exception as e:
        # Catch any other exceptions to prevent app failure
        error_msg = f"Unexpected error: {str(e)}"
        logger.exception(f"Unexpected error extracting schema from {db_path}")
        return GetSqliteSchemaResponse(error=error_msg).model_dump()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Example usage
    db_path = input("Enter SQLite database path: ")
    if not db_path:
        db_path = '../user_files/sakila.db'
    
    # Call the function
    schema_info = get_sqlite_schema(db_path)
    
    # Just print the result with minimal formatting
    print(schema_info)
