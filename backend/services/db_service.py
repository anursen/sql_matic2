from backend.models.data_models import DatabaseStructure, Database, Table, Column


class DatabaseService:
    """Service to manage database structures"""
    
    def __init__(self):
        # Create a mock database structure
        self.db_structure = DatabaseStructure(
            databases=[
                Database(
                    name="Sample Database",
                    tables=[
                        Table(
                            name="users",
                            columns=[
                                Column(name="id", type="INT PRIMARY KEY"),
                                Column(name="username", type="VARCHAR(50)"),
                                Column(name="email", type="VARCHAR(100)"),
                                Column(name="created_at", type="TIMESTAMP")
                            ]
                        ),
                        Table(
                            name="products",
                            columns=[
                                Column(name="id", type="INT PRIMARY KEY"),
                                Column(name="name", type="VARCHAR(100)"),
                                Column(name="price", type="DECIMAL(10,2)"),
                                Column(name="category_id", type="INT")
                            ]
                        )
                    ]
                )
            ]
        )
    
    def get_structure(self) -> DatabaseStructure:
        """Get the database structure"""
        return self.db_structure


# Create a singleton instance
db_service = DatabaseService()
