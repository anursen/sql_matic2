import os
import sys
import pytest
import tempfile
import sqlite3
from pathlib import Path

# Setup proper Python path for imports
# This allows imports to work regardless of where the test is run from
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

# Import directly from the tools directory without using the 'backend' package name
# This makes the import more resilient to path issues
from backend.tools.sqlite_execute_query import execute_sqlite_query

# Skip these tests if the module can't be imported
pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

# Setup test database
@pytest.fixture
def test_db_path():
    """Create a temporary SQLite database for testing"""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.db')
    
    # Connect and create test tables/data
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    # Create a test table with sample data
    cursor.execute('''
    CREATE TABLE test_table (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        value REAL,
        description TEXT
    )
    ''')
    
    # Insert some test data
    test_data = [
        (1, 'Item 1', 10.5, 'First test item'),
        (2, 'Item 2', 20.75, 'Second test item'),
        (3, 'Item 3', 30.0, 'Third test item with "quotes"'),
        (4, 'Item 4', 40.25, "Fourth test item with 'quotes'"),
        (5, 'Item 5', 50.5, 'Fifth test item')
    ]
    
    cursor.executemany(
        'INSERT INTO test_table (id, name, value, description) VALUES (?, ?, ?, ?)',
        test_data
    )
    
    # Create another table for joins
    cursor.execute('''
    CREATE TABLE test_categories (
        id INTEGER PRIMARY KEY,
        category_name TEXT NOT NULL
    )
    ''')
    
    # Insert category data
    categories = [
        (1, 'Category A'),
        (2, 'Category B'),
        (3, 'Category C')
    ]
    
    cursor.executemany(
        'INSERT INTO test_categories (id, category_name) VALUES (?, ?)',
        categories
    )
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    os.close(fd)  # Close the file descriptor
    
    yield path  # Return the path for tests to use
    
    # Clean up after tests
    try:
        os.unlink(path)
    except Exception as e:
        print(f"Warning: Could not delete temporary test database: {e}")


class TestSqliteExecuteQuery:
    """Test suite for the SQLite query execution tool"""

    def test_select_query(self, test_db_path):
        """Test a basic SELECT query"""
        # Prepare input for the tool
        tool_input = {
            "db_path": test_db_path,
            "query": "SELECT * FROM test_table ORDER BY id"
        }
        
        # Execute query
        result = execute_sqlite_query.invoke(tool_input)
        
        # Assertions
        assert "error" not in result or result["error"] is None
        assert "results" in result
        assert len(result["results"]) == 1  # One query result
        assert result["results"][0]["row_count"] == 5  # Five rows returned
        assert "id" in result["results"][0]["columns"]
        assert "name" in result["results"][0]["columns"]
        assert "value" in result["results"][0]["columns"]
        assert "description" in result["results"][0]["columns"]
        assert result["results"][0]["is_select"] == True

    def test_filtered_query(self, test_db_path):
        """Test a SELECT query with filtering"""
        # Prepare input for the tool
        tool_input = {
            "db_path": test_db_path,
            "query": "SELECT * FROM test_table WHERE value > 30 ORDER BY id"
        }
        
        # Execute query
        result = execute_sqlite_query.invoke(tool_input)
        
        # Assertions
        assert "error" not in result or result["error"] is None
        assert result["results"][0]["row_count"] == 2  # Two rows (Item 4, Item 5)
        assert result["results"][0]["rows"][0][0] == 4  # First row id should be 4
        assert result["results"][0]["rows"][1][0] == 5  # Second row id should be 5

    def test_join_query(self, test_db_path):
        """Test a JOIN query across multiple tables"""
        # Prepare input for the tool
        tool_input = {
            "db_path": test_db_path,
            "query": """
            SELECT t.id, t.name, c.category_name 
            FROM test_table t
            JOIN test_categories c ON t.id = c.id
            WHERE t.id <= 3
            ORDER BY t.id
            """
        }
        
        # Execute query
        result = execute_sqlite_query.invoke(tool_input)
        
        # Assertions
        assert "error" not in result or result["error"] is None
        assert result["results"][0]["row_count"] == 3  # Three matching rows
        assert len(result["results"][0]["columns"]) == 3  # Three columns
        # Check that correct category names are matched
        rows = result["results"][0]["rows"]
        assert rows[0][2] == "Category A"  # First row should have Category A
        assert rows[1][2] == "Category B"  # Second row should have Category B

    def test_multiple_queries(self, test_db_path):
        """Test executing multiple queries at once"""
        # Prepare input for the tool
        tool_input = {
            "db_path": test_db_path,
            "query": """
            SELECT COUNT(*) FROM test_table;
            SELECT COUNT(*) FROM test_categories;
            """
        }
        
        # Execute query
        result = execute_sqlite_query.invoke(tool_input)
        
        # Assertions
        assert "error" not in result or result["error"] is None
        assert len(result["results"]) == 2  # Two result sets
        assert result["results"][0]["rows"][0][0] == 5  # 5 rows in test_table
        assert result["results"][1]["rows"][0][0] == 3  # 3 rows in test_categories

    def test_parameterized_query(self, test_db_path):
        """Test a query with parameters"""
        # Prepare input with parameters
        tool_input = {
            "db_path": test_db_path,
            "query": "SELECT * FROM test_table WHERE value > :min_value AND value < :max_value ORDER BY id",
            "params": {"min_value": 20, "max_value": 45}
        }
        
        # Execute query
        result = execute_sqlite_query.invoke(tool_input)
        
        # Assertions
        assert "error" not in result or result["error"] is None
        
        # Update assertion to match actual result (3 rows instead of 2)
        assert result["results"][0]["row_count"] == 3
        
        # Check that Items 2, 3, and 4 are in the results (all have values between 20 and 45)
        items = [row[1] for row in result["results"][0]["rows"]]
        assert "Item 2" in items  # value: 20.75
        assert "Item 3" in items  # value: 30.0
        assert "Item 4" in items  # value: 40.25
        
        # Verify the values are actually within our range
        values = [row[2] for row in result["results"][0]["rows"]]
        for value in values:
            assert 20 < value < 45

    def test_max_rows_limit(self, test_db_path):
        """Test the max_rows parameter to limit returned rows"""
        # Prepare input with max_rows
        tool_input = {
            "db_path": test_db_path,
            "query": "SELECT * FROM test_table ORDER BY id",
            "max_rows": 2
        }
        
        # Execute query
        result = execute_sqlite_query.invoke(tool_input)
        
        # Assertions
        assert "error" not in result or result["error"] is None
        assert result["results"][0]["row_count"] == 2  # Only two rows returned
        assert result["results"][0]["rows"][0][0] == 1  # First row should be id 1
        assert result["results"][0]["rows"][1][0] == 2  # Second row should be id 2

    def test_nonexistent_db(self, tmp_path):
        """Test behavior with a non-existent database"""
        nonexistent_path = str(tmp_path / "nonexistent.db")
        
        # Prepare input for the tool
        tool_input = {
            "db_path": nonexistent_path,
            "query": "SELECT * FROM test_table"
        }
        
        # Execute query
        result = execute_sqlite_query.invoke(tool_input)
        
        # Assertions
        assert "error" in result
        assert result["error"] is not None
        assert "not found" in result["error"].lower()

    def test_invalid_query(self, test_db_path):
        """Test behavior with an invalid SQL query"""
        # Prepare input with invalid SQL
        tool_input = {
            "db_path": test_db_path,
            "query": "SELECT * FROMM test_table"  # Deliberate typo
        }
        
        # Execute query
        result = execute_sqlite_query.invoke(tool_input)
        
        # Assertions
        assert "error" in result
        assert result["error"] is not None
        assert "sqlite error" in result["error"].lower()
