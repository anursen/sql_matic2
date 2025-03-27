from fastapi import APIRouter, HTTPException, Depends
from typing import List
import os

# Import our models and tools
from models.data_models import SQLiteSchemaAllResponse, SchemaTableInfo, SchemaColumnInfo, SchemaIndexInfo
from tools.sqlite_get_schema_all import sqlite_get_schema_all
from config.config import config
from utils.logger import logger

# Create or use existing router
router = APIRouter()

@router.get("/database/schema", response_model=SQLiteSchemaAllResponse, 
            summary="Get complete database schema", 
            description="Returns the complete schema of the connected SQLite database in a structured format")
async def get_database_schema():
    """
    Get the complete schema of the currently connected SQLite database.
    Returns table structures with columns, keys, and indices.
    """
    try:
        # Get database path from configuration
        db_path = config.get("query_db", "path")
        
        # Log the request
        logger.info(f"Retrieving complete database schema from {db_path}")
        
        # Check if database exists
        if not os.path.exists(db_path):
            logger.error(f"Database not found at path: {db_path}")
            return SQLiteSchemaAllResponse(
                tables=[],
                database_path=db_path,
                error="Database file not found"
            )
        
        # Call our schema extraction function
        schema_data = sqlite_get_schema_all()
        
        # Convert to Pydantic models (this validates the data structure)
        tables = []
        for table_data in schema_data:
            tables.append(SchemaTableInfo.model_validate(table_data))
        
        # Return the response
        return SQLiteSchemaAllResponse(
            tables=tables,
            database_path=db_path
        )
        
    except Exception as e:
        logger.exception(f"Error retrieving database schema: {str(e)}")
        # Return error response
        return SQLiteSchemaAllResponse(
            tables=[],
            database_path=config.get("query_db", "path", ""),
            error=str(e)
        )