import sqlite3
import os
import sys
import json
from typing import List, Dict, Any, Optional

# Add parent directory to path to ensure imports work correctly
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

# Import configuration and logging
from config.config import config
from utils.logger import logger

def sqlite_get_schema_all() -> List[Dict[str, Any]]:
    """
    Extracts the complete schema information from a SQLite database as an array in JSON format.
    Each array element represents a table with its columns and their properties.
    
    Returns:
        List[Dict[str, Any]]: A list of table schemas with column details
    """
    try:
        db_path = config.get("query_db", "path")
        logger.info(f"Extracting complete schema from SQLite database: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        schema_array = []
        
        # Process each table
        for table_name in all_tables:
            table_schema = {
                "table_name": table_name,
                "columns": []
            }
            
            # Get column information
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_data = cursor.fetchall()
            
            # Get foreign key information
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            fk_data = cursor.fetchall()
            
            # Create a mapping of column names to their foreign key info
            fk_map = {}
            for fk in fk_data:
                # Foreign key data: id, seq, table, from, to, on_update, on_delete, match
                fk_map[fk[3]] = {
                    "referenced_table": fk[2],  
                    "referenced_column": fk[4],
                    "on_update": fk[5],
                    "on_delete": fk[6]
                }
            
            # Process column information
            for col in columns_data:
                # Column data: cid, name, type, notnull, dflt_value, pk
                col_id = col[0]
                col_name = col[1]
                col_type = col[2]
                not_null = bool(col[3])
                default_value = col[4]
                is_pk = bool(col[5])
                
                is_fk = col_name in fk_map
                references = None
                
                if is_fk:
                    references = fk_map[col_name]
                
                column_info = {
                    "name": col_name,
                    "type": col_type,
                    "not_null": not_null,
                    "default_value": default_value,
                    "is_primary_key": is_pk,
                    "is_foreign_key": is_fk
                }
                
                if is_fk:
                    column_info["references"] = references
                
                table_schema["columns"].append(column_info)
            
            # Get index information
            cursor.execute(f"PRAGMA index_list({table_name})")
            indices = cursor.fetchall()
            
            if indices:
                table_schema["indices"] = []
                for idx in indices:
                    # Index data: seq, name, unique
                    index_name = idx[1]
                    is_unique = bool(idx[2])
                    
                    # Get the columns in this index
                    cursor.execute(f"PRAGMA index_info({index_name})")
                    index_columns = cursor.fetchall()
                    column_names = [table_schema["columns"][col[1]]["name"] for col in index_columns]
                    
                    table_schema["indices"].append({
                        "name": index_name,
                        "unique": is_unique,
                        "columns": column_names
                    })
            
            schema_array.append(table_schema)
        
        conn.close()
        return schema_array
    
    except Exception as e:
        logger.error(f"Error extracting SQLite schema: {str(e)}")
        return []

if __name__ == "__main__":
    # Example standalone usage
    schema = sqlite_get_schema_all()
    print(json.dumps(schema, indent=2))
