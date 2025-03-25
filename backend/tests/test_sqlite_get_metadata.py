import os
import sys
import pytest
import tempfile
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Setup proper Python path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

# Import the function to test
from backend.tools.sqlite_get_metadata import get_sqlite_metadata

# Skip these tests if the module can't be imported
pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

# Setup test database
@pytest.fixture
def test_db_path():
    """Create a temporary SQLite database for testing metadata extraction"""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.db')
    
    # Connect and create test tables/data
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    # Create first test table with sample data
    cursor.execute('''
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT,
        address TEXT,
        signup_date TEXT
    )
    ''')
    
    # Insert customer data
    customer_data = []
    for i in range(1, 51):  # 50 customers
        customer_data.append((
            i,
            f"Customer {i}",
            f"customer{i}@example.com",
            f"555-{100+i}",
            f"Address {i}, City",
            datetime.now().isoformat()
        ))
    
    cursor.executemany(
        'INSERT INTO customers (id, name, email, phone, address, signup_date) VALUES (?, ?, ?, ?, ?, ?)',
        customer_data
    )
    
    # Create a second table with foreign key relationship
    cursor.execute('''
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        order_date TEXT,
        total_amount REAL,
        status TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    )
    ''')
    
    # Insert order data
    order_data = []
    for i in range(1, 201):  # 200 orders
        customer_id = ((i - 1) % 50) + 1  # Distribute orders among customers
        order_data.append((
            i,
            customer_id,
            datetime.now().isoformat(),
            float(i * 10.5),
            "COMPLETED" if i % 4 != 0 else "PENDING"
        ))
    
    cursor.executemany(
        'INSERT INTO orders (id, customer_id, order_date, total_amount, status) VALUES (?, ?, ?, ?, ?)',
        order_data
    )
    
    # Create a table with various data types
    cursor.execute('''
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        price REAL,
        stock INTEGER,
        is_available BOOLEAN,
        created_at TEXT,
        image_data BLOB
    )
    ''')
    
    # Insert product data with different data types
    products_data = []
    for i in range(1, 31):  # 30 products
        products_data.append((
            i,
            f"Product {i}",
            f"Description for product {i} with details",
            float(i * 15.99),
            i * 5,
            i % 2 == 0,  # Even numbered products are available
            datetime.now().isoformat(),
            bytes(f"Dummy binary data for product {i}", 'utf-8')  # Simple BLOB data
        ))
    
    cursor.executemany(
        'INSERT INTO products (id, name, description, price, stock, is_available, created_at, image_data) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        products_data
    )
    
    # Create an index on the orders table
    cursor.execute('CREATE INDEX idx_customer_id ON orders(customer_id)')
    
    # Create another index on products
    cursor.execute('CREATE INDEX idx_product_name ON products(name)')
    
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


class TestSqliteGetMetadata:
    """Test suite for the SQLite metadata extraction tool"""

    def test_basic_metadata_extraction(self, test_db_path):
        """Test basic metadata extraction from a SQLite database"""
        # Execute the metadata extraction
        result = get_sqlite_metadata.invoke(test_db_path)
        
        # Assertions for database info
        assert "error" not in result or result["error"] is None
        assert "database_info" in result
        assert result["database_info"]["name"] == os.path.basename(test_db_path)
        assert result["database_info"]["path"] == test_db_path
        assert result["database_info"]["size_bytes"] > 0
        assert "page_size" in result["database_info"]
        assert "page_count" in result["database_info"]
        
        # Assertions for table stats
        assert "table_stats" in result
        assert len(result["table_stats"]) == 3  # Should have three tables
        
        # Check if our tables are present
        table_names = [table["name"] for table in result["table_stats"]]
        assert "customers" in table_names
        assert "orders" in table_names
        assert "products" in table_names
        
        # Check row counts
        customers_table = next(t for t in result["table_stats"] if t["name"] == "customers")
        orders_table = next(t for t in result["table_stats"] if t["name"] == "orders")
        products_table = next(t for t in result["table_stats"] if t["name"] == "products")
        
        assert customers_table["row_count"] == 50
        assert orders_table["row_count"] == 200
        assert products_table["row_count"] == 30
        
        # Check column counts
        assert customers_table["column_count"] == 6
        assert orders_table["column_count"] == 5
        assert products_table["column_count"] == 8
        
        # Check for index counts
        assert orders_table["index_count"] >= 1  # Should have at least the index we created
        assert products_table["index_count"] >= 1  # Should have the index we created
        
        # Check overall statistics
        assert "stats" in result
        assert result["stats"]["databaseCount"] == 1
        assert result["stats"]["tableCount"] == 3
        assert result["stats"]["rowCount"] == 280  # 50 + 200 + 30 = 280

    def test_size_estimation(self, test_db_path):
        """Test that size estimation for tables works correctly"""
        # Execute the metadata extraction
        result = get_sqlite_metadata.invoke(test_db_path)
        
        # Check size estimations
        for table_info in result["table_stats"]:
            # Every table should have size estimations
            assert "estimated_size_bytes" in table_info
            assert "estimated_size_human" in table_info
            
            # Size should be non-zero for tables with data
            assert table_info["estimated_size_bytes"] > 0
            
            # Tables with more rows should have larger sizes
            if table_info["name"] == "orders":
                # Orders has the most rows, so should have largest size
                orders_size = table_info["estimated_size_bytes"]
            if table_info["name"] == "customers":
                customers_size = table_info["estimated_size_bytes"]
        
        # Orders table should be larger than customers (more rows)
        assert orders_size > customers_size

    def test_empty_database(self):
        """Test metadata extraction from an empty database"""
        # Create a new empty database
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            # Just create the database file without any tables
            conn = sqlite3.connect(path)
            conn.close()
            
            # Execute the metadata extraction
            result = get_sqlite_metadata.invoke(path)
            
            # Basic assertions
            assert "error" not in result or result["error"] is None
            assert "database_info" in result
            assert result["database_info"]["name"] == os.path.basename(path)
            assert "table_stats" in result
            assert len(result["table_stats"]) == 0  # No tables
            assert result["stats"]["tableCount"] == 0
            assert result["stats"]["rowCount"] == 0
            
        finally:
            # Clean up
            os.unlink(path)

    def test_nonexistent_database(self, tmp_path):
        """Test behavior with a non-existent database file"""
        nonexistent_path = str(tmp_path / "does_not_exist.db")
        
        # Execute the metadata extraction
        result = get_sqlite_metadata.invoke(nonexistent_path)
        
        # Should return an error
        assert "error" in result
        assert result["error"] is not None
        assert "not found" in result["error"].lower()
        
        # Should have empty metadata
        assert "database_info" in result
        assert not result["database_info"]  # Empty dict
        assert "table_stats" in result
        assert len(result["table_stats"]) == 0
        assert result["stats"]["tableCount"] == 0

    def test_corrupt_database(self, tmp_path):
        """Test behavior with a corrupt database file"""
        corrupt_path = str(tmp_path / "corrupt.db")
        
        # Create a file with invalid SQLite content
        with open(corrupt_path, 'w') as f:
            f.write("This is not a valid SQLite database file")
        
        # Execute the metadata extraction
        result = get_sqlite_metadata.invoke(corrupt_path)
        
        # Should return an error
        assert "error" in result
        assert result["error"] is not None
        assert "sqlite" in result["error"].lower()
        
        # Should have empty metadata
        assert "database_info" in result
        assert not result["database_info"] or result["database_info"].get("name")  # May have the filename
        assert "table_stats" in result
        assert len(result["table_stats"]) == 0

    def test_file_info_accuracy(self, test_db_path):
        """Test that file info (size, dates) is accurate"""
        # Get actual file information
        actual_size = os.path.getsize(test_db_path)
        actual_mtime = os.path.getmtime(test_db_path)
        
        # Execute the metadata extraction
        result = get_sqlite_metadata.invoke(test_db_path)
        
        # Check file information accuracy
        assert result["database_info"]["size_bytes"] == actual_size
        
        # The modification time should be parsed from the stored ISO string
        db_mtime = datetime.fromisoformat(result["database_info"]["modification_time"]).timestamp()
        
        # Allow small difference due to timestamp precision/conversion
        assert abs(db_mtime - actual_mtime) < 2
