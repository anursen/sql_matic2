import os
import sys
import pytest
import tempfile
import sqlite3
from pathlib import Path

# Setup proper Python path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

# Import the function to test
from backend.tools.sqlite_get_schema import get_sqlite_schema

# Skip these tests if the module can't be imported
pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

# Setup test database
@pytest.fixture
def test_db_path():
    """Create a temporary SQLite database for testing schema extraction"""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.db')
    
    # Connect and create test tables/data
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    # Create a simple users table with primary key
    cursor.execute('''
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        email TEXT,
        created_at TEXT,
        status TEXT DEFAULT 'active'
    )
    ''')
    
    # Create a table with foreign key relationship
    cursor.execute('''
    CREATE TABLE posts (
        post_id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT,
        published_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    # Create a table with multiple foreign keys
    cursor.execute('''
    CREATE TABLE comments (
        comment_id INTEGER PRIMARY KEY,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT,
        FOREIGN KEY (post_id) REFERENCES posts(post_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    # Create a view
    cursor.execute('''
    CREATE VIEW active_users AS
    SELECT user_id, username, email
    FROM users
    WHERE status = 'active'
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX idx_posts_user_id ON posts(user_id)')
    cursor.execute('CREATE INDEX idx_comments_post_id ON comments(post_id)')
    cursor.execute('CREATE INDEX idx_comments_user_id ON comments(user_id)')
    
    # Insert some sample data
    cursor.executemany(
        'INSERT INTO users (user_id, username, email, created_at, status) VALUES (?, ?, ?, ?, ?)',
        [
            (1, 'user1', 'user1@example.com', '2023-01-01', 'active'),
            (2, 'user2', 'user2@example.com', '2023-01-02', 'active'),
            (3, 'user3', 'user3@example.com', '2023-01-03', 'inactive')
        ]
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


class TestSqliteGetSchema:
    """Test suite for the SQLite schema extraction tool"""

    def test_basic_schema_extraction(self, test_db_path):
        """Test basic schema extraction from a SQLite database"""
        # Extract the schema
        result = get_sqlite_schema.invoke(test_db_path)
        
        # Basic assertions for successful execution
        assert "error" not in result or result["error"] is None
        assert "database_schema" in result
        assert "tables" in result
        
        # Check if tables list includes all expected tables and views
        assert len(result["tables"]) == 4  # 3 tables + 1 view
        assert "users" in result["tables"]
        assert "posts" in result["tables"]
        assert "comments" in result["tables"]
        assert "active_users" in result["tables"]
        
        # Check database structure details
        db_schema = result["database_schema"]
        assert "databases" in db_schema
        assert len(db_schema["databases"]) == 1
        
        # Get the database
        database = db_schema["databases"][0]
        assert database["name"] == os.path.basename(test_db_path)
        assert "tables" in database
        
        # Get tables from structure
        tables = {table["name"]: table for table in database["tables"]}
        
        # Check if all tables are included in the structure
        assert "users" in tables
        assert "posts" in tables
        assert "comments" in tables
        assert "active_users" in tables
        
        # Check column details for users table
        users_columns = {col["name"]: col for col in tables["users"]["columns"]}
        assert "user_id" in users_columns
        assert "username" in users_columns
        assert "email" in users_columns
        assert "created_at" in users_columns
        assert "status" in users_columns
        
        # Verify primary key is correctly identified
        assert users_columns["user_id"]["primary_key"] == True
        
        # Check foreign key relationships
        posts_columns = {col["name"]: col for col in tables["posts"]["columns"]}
        assert posts_columns["user_id"]["foreign_key"] == True
        assert posts_columns["user_id"]["references"]["table"] == "users"
        assert posts_columns["user_id"]["references"]["column"] == "user_id"
        
        # Check multiple foreign keys in comments table
        comments_columns = {col["name"]: col for col in tables["comments"]["columns"]}
        assert comments_columns["post_id"]["foreign_key"] == True
        assert comments_columns["post_id"]["references"]["table"] == "posts"
        assert comments_columns["post_id"]["references"]["column"] == "post_id"
        
        assert comments_columns["user_id"]["foreign_key"] == True
        assert comments_columns["user_id"]["references"]["table"] == "users"
        assert comments_columns["user_id"]["references"]["column"] == "user_id"

    def test_empty_database(self):
        """Test schema extraction from an empty database"""
        # Create a new empty database
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            # Just create the database file without any tables
            conn = sqlite3.connect(path)
            conn.close()
            
            # Extract the schema
            result = get_sqlite_schema.invoke(path)
            
            # Basic assertions
            assert "error" not in result or result["error"] is None
            assert "database_schema" in result
            assert "tables" in result
            assert len(result["tables"]) == 0  # No tables
            
            # Check empty database structure
            db_schema = result["database_schema"]
            assert "databases" in db_schema
            assert len(db_schema["databases"]) == 1
            
            # Database should have no tables
            database = db_schema["databases"][0]
            assert database["name"] == os.path.basename(path)
            assert "tables" in database
            assert len(database["tables"]) == 0
            
        finally:
            # Clean up
            os.unlink(path)

    def test_nonexistent_database(self, tmp_path):
        """Test behavior with a non-existent database file"""
        nonexistent_path = str(tmp_path / "does_not_exist.db")
        
        # Extract the schema
        result = get_sqlite_schema.invoke(nonexistent_path)
        
        # Should return an error
        assert "error" in result
        assert result["error"] is not None
        assert "not found" in result["error"].lower()
        
        # Check for empty schema structure (now returned instead of missing)
        assert "database_schema" in result
        assert "databases" in result["database_schema"]
        assert len(result["database_schema"]["databases"]) == 0
        assert "tables" in result
        assert len(result["tables"]) == 0

    def test_corrupt_database(self, tmp_path):
        """Test behavior with a corrupt database file"""
        corrupt_path = str(tmp_path / "corrupt.db")
        
        # Create a file with invalid SQLite content
        with open(corrupt_path, 'w') as f:
            f.write("This is not a valid SQLite database file")
        
        # Extract the schema
        result = get_sqlite_schema.invoke(corrupt_path)
        
        # Should return an error
        assert "error" in result
        assert result["error"] is not None
        assert "sqlite" in result["error"].lower()

    def test_complex_schema(self, test_db_path):
        """Test extraction of a more complex schema with additional tables"""
        # Add more complex schema elements to the test database
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        # Create a table with composite primary key
        cursor.execute('''
        CREATE TABLE tags (
            tag_id INTEGER,
            name TEXT,
            category TEXT,
            PRIMARY KEY (tag_id, name)
        )
        ''')
        
        # Create a many-to-many relationship table
        cursor.execute('''
        CREATE TABLE post_tags (
            post_id INTEGER,
            tag_id INTEGER,
            tag_name TEXT,
            PRIMARY KEY (post_id, tag_id, tag_name),
            FOREIGN KEY (post_id) REFERENCES posts(post_id),
            FOREIGN KEY (tag_id, tag_name) REFERENCES tags(tag_id, name)
        )
        ''')
        
        conn.close()
        
        # Extract the schema
        result = get_sqlite_schema.invoke(test_db_path)
        
        # Basic assertions for successful execution
        assert "error" not in result or result["error"] is None
        assert "database_schema" in result
        assert "tables" in result
        
        # Check if tables list includes the new tables
        assert len(result["tables"]) == 6  # 5 tables + 1 view
        assert "tags" in result["tables"]
        assert "post_tags" in result["tables"]
        
        # Get tables from structure
        db_schema = result["database_schema"]
        database = db_schema["databases"][0]
        tables = {table["name"]: table for table in database["tables"]}
        
        # Check composite primary key table
        assert "tags" in tables
        tags_columns = {col["name"]: col for col in tables["tags"]["columns"]}
        
        # Check the many-to-many relationship table
        assert "post_tags" in tables
        post_tags_columns = {col["name"]: col for col in tables["post_tags"]["columns"]}
        
        # Verify foreign key relationships
        assert post_tags_columns["post_id"]["foreign_key"] == True
        assert post_tags_columns["post_id"]["references"]["table"] == "posts"
