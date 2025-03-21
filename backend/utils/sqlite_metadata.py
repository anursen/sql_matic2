import sqlite3
import os

class SQLiteMetadata:
    def __init__(self, db_path):
        """
        Initialize the SQLiteMetadata class with a database path.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")
        
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establishes connection to the database"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
    
    def close(self):
        """Closes the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def get_metadata(self):
        """
        Returns comprehensive metadata about the SQLite database structure.
        
        Returns:
            dict: A dictionary containing database metadata
        """
        try:
            self.connect()
            
            # Get file size
            db_size = os.path.getsize(self.db_path)
            
            # Get list of tables
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            table_names = [row[0] for row in self.cursor.fetchall()]
            
            tables = []
            total_rows = 0
            
            # Gather information for each table
            for table_name in table_names:
                # Get row count
                self.cursor.execute(f"SELECT COUNT(*) FROM '{table_name}';")
                row_count = self.cursor.fetchone()[0]
                total_rows += row_count
                
                # Get column information
                self.cursor.execute(f"PRAGMA table_info('{table_name}');")
                columns = []
                for col in self.cursor.fetchall():
                    columns.append({
                        "name": col[1],
                        "type": col[2],
                        "notnull": bool(col[3]),
                        "default_value": col[4],
                        "primary_key": bool(col[5])
                    })
                
                # Estimate table size (this is approximate in SQLite)
                avg_row_size = 0
                if row_count > 0:
                    try:
                        self.cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 1;")
                        sample_row = self.cursor.fetchone()
                        if sample_row:
                            # Rough estimation of row size in bytes
                            avg_row_size = sum(len(str(cell)) for cell in sample_row if cell is not None)
                    except sqlite3.OperationalError:
                        # Handle case where table might be virtual or have other issues
                        pass
                
                estimated_size = avg_row_size * row_count
                
                tables.append({
                    "name": table_name,
                    "row_count": row_count,
                    "column_count": len(columns),
                    "columns": columns,
                    "estimated_size_bytes": estimated_size
                })
            
            # Get database page size and other PRAGMA information
            self.cursor.execute("PRAGMA page_size;")
            page_size = self.cursor.fetchone()[0]
            
            self.cursor.execute("PRAGMA page_count;")
            page_count = self.cursor.fetchone()[0]
            
            return {
                "file_path": self.db_path,
                "file_size_bytes": db_size,
                "page_size": page_size,
                "page_count": page_count,
                "total_rows": total_rows,
                "tables_count": len(tables),
                "tables": tables
            }
        finally:
            self.close()

    def get_schema(self):
        """
        Returns the SQL schema of the database, including CREATE statements for tables,
        indexes, views, and triggers.
        
        Returns:
            dict: A dictionary containing schema information for all objects
        """
        try:
            self.connect()
            
            # Query to get all database objects
            self.cursor.execute("""
                SELECT type, name, sql FROM sqlite_master 
                WHERE sql IS NOT NULL
                ORDER BY type, name;
            """)
            
            schema = {
                "tables": [],
                "indexes": [],
                "views": [],
                "triggers": []
            }
            
            for obj_type, obj_name, obj_sql in self.cursor.fetchall():
                if obj_type == 'table':
                    # Get foreign key information
                    self.cursor.execute(f"PRAGMA foreign_key_list('{obj_name}');")
                    foreign_keys = []
                    for fk in self.cursor.fetchall():
                        foreign_keys.append({
                            "id": fk[0],
                            "seq": fk[1],
                            "table": fk[2],
                            "from": fk[3],
                            "to": fk[4],
                            "on_update": fk[5],
                            "on_delete": fk[6],
                            "match": fk[7]
                        })
                    
                    # Get indices for the table
                    self.cursor.execute(f"PRAGMA index_list('{obj_name}');")
                    indices = []
                    for idx in self.cursor.fetchall():
                        idx_name = idx[1]
                        self.cursor.execute(f"PRAGMA index_info('{idx_name}');")
                        idx_columns = [col[2] for col in self.cursor.fetchall()]
                        indices.append({
                            "name": idx_name,
                            "unique": bool(idx[2]),
                            "columns": idx_columns
                        })
                    
                    schema["tables"].append({
                        "name": obj_name,
                        "sql": obj_sql,
                        "foreign_keys": foreign_keys,
                        "indices": indices
                    })
                
                elif obj_type == 'index':
                    schema["indexes"].append({
                        "name": obj_name,
                        "sql": obj_sql
                    })
                
                elif obj_type == 'view':
                    schema["views"].append({
                        "name": obj_name,
                        "sql": obj_sql
                    })
                
                elif obj_type == 'trigger':
                    schema["triggers"].append({
                        "name": obj_name,
                        "sql": obj_sql
                    })
            
            return schema
        finally:
            self.close()


if __name__ == "__main__":
    while True:
        print("\nSQLite Database Analyzer")
        print("------------------------")
        
        # Get database path from user
        db_path = input("Enter SQLite database path (or 'exit' to quit): ")
        db_path = 'backend/whosonfirst-data-constituency-latest.db'
        if db_path.lower() == 'exit':
            break
        
        # Check if file exists
        if not os.path.exists(db_path):
            print(f"Error: File '{db_path}' not found.")
            continue
        
        try:
            analyzer = SQLiteMetadata(db_path)
            
            while True:
                print("\nChoose an option:")
                print("1. Get database metadata (tables, rows, sizes)")
                print("2. Get database schema (SQL statements)")
                print("3. Select a different database")
                print("4. Exit")
                
                choice = input("Enter your choice (1-4): ")
                
                if choice == '1':
                    metadata = analyzer.get_metadata()
                    print(f"\nDatabase: {metadata['file_path']}")
                    print(f"Size: {metadata['file_size_bytes'] / 1024:.2f} KB")
                    print(f"Tables: {metadata['tables_count']}")
                    print(f"Total rows: {metadata['total_rows']}")
                    print("\nTable details:")
                    for table in metadata['tables']:
                        print(f"  - {table['name']}: {table['row_count']} rows, {table['column_count']} columns, "
                              f"~{table['estimated_size_bytes'] / 1024:.2f} KB")
                        print("    Columns:")
                        for col in table['columns']:
                            pk_mark = " (PK)" if col['primary_key'] else ""
                            null_mark = " NOT NULL" if col['notnull'] else ""
                            print(f"      - {col['name']}: {col['type']}{null_mark}{pk_mark}")
                
                elif choice == '2':
                    schema = analyzer.get_schema()
                    
                    print("\nTables:")
                    for table in schema['tables']:
                        print(f"\n-- Table: {table['name']}")
                        print(table['sql'])
                        
                        if table['foreign_keys']:
                            print("\n  Foreign Keys:")
                            for fk in table['foreign_keys']:
                                print(f"    - {fk['from']} -> {fk['table']}({fk['to']})")
                    
                    if schema['indexes']:
                        print("\nIndexes:")
                        for idx in schema['indexes']:
                            print(f"\n-- Index: {idx['name']}")
                            print(idx['sql'])
                    
                    if schema['views']:
                        print("\nViews:")
                        for view in schema['views']:
                            print(f"\n-- View: {view['name']}")
                            print(view['sql'])
                    
                    if schema['triggers']:
                        print("\nTriggers:")
                        for trigger in schema['triggers']:
                            print(f"\n-- Trigger: {trigger['name']}")
                            print(trigger['sql'])
                
                elif choice == '3':
                    break
                
                elif choice == '4':
                    print("Exiting program.")
                    exit(0)
                
                else:
                    print("Invalid choice. Please enter a number between 1 and 4.")
                
        except Exception as e:
            print(f"Error: {e}")
