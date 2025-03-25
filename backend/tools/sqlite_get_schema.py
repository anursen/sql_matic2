import sqlite3
import sys
import os
from langchain_core.tools import tool

# Add parent directory to path to ensure imports work correctly
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)


# Import configuration and logging
from config.config import config
from utils.logger import logger
from models.data_models import GetSqliteSchemaRequest, GetSqliteSchemaResponse, TableInfo, ColumnInfo


@tool(args_schema=GetSqliteSchemaRequest)
def sqlite_get_schema(table_count: int = 0) -> GetSqliteSchemaResponse:
    """
    Extracts the complete schema information from a SQLite database.
    
    Args:
        table_count: Limit the number of tables to return (0 for all)
        
    Returns:
        A structured response containing the database schema information
    """
    try:
        db_path = config.get("query_db", "path")
        logger.info(f"Extracting schema from SQLite database: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        # Limit table count if specified
        tables_to_process = all_tables
        if table_count > 0:
            tables_to_process = all_tables[:table_count]
        
        schema_info = GetSqliteSchemaResponse(database_path=db_path)
        
        # Process each table
        for table_name in tables_to_process:
            table_info = TableInfo(name=table_name)
            
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
                fk_map[fk[3]] = (fk[2], fk[4])  # (ref_table, ref_column)
            
            # Process column information
            for col in columns_data:
                # Column data: cid, name, type, notnull, dflt_value, pk
                col_name = col[1]
                col_type = col[2]
                is_pk = col[5] == 1
                
                is_fk = col_name in fk_map
                references = None
                
                if is_fk:
                    ref_table, ref_column = fk_map[col_name]
                    references = f"{ref_table}.{ref_column}"
                
                column_info = ColumnInfo(
                    name=col_name,
                    data_type=col_type,
                    is_primary_key=is_pk,
                    is_foreign_key=is_fk,
                    references=references
                )
                
                table_info.columns.append(column_info)
            
            schema_info.tables.append(table_info)
        
        conn.close()
        return schema_info
    
    except Exception as e:
        logger.error(f"Error extracting SQLite schema: {str(e)}")
        return GetSqliteSchemaResponse(
            database_path=config.get("query_db", "path"),
            error=str(e)
        )


if __name__ == "__main__":
    # Example standalone usage
    result = sqlite_get_schema.invoke({'table_count':0})  # Change table_count as needed
    
    # Print the schema in the requested format
    for table in result.tables:
        print(f"\nTable: {table.name}")
        print("-" * 60)
        for column in table.columns:
            fk_info = f" FK [{column.references}]" if column.is_foreign_key else ""
            pk_info = " PK" if column.is_primary_key else ""
            print(f"{column.name} {column.data_type}{pk_info}{fk_info}")
