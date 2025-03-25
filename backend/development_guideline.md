Default Guidelines for Function Development
This document outlines standard guidelines for creating functions in our application. Following these principles ensures consistency, robustness, and maintainability across the codebase.

1. Centralized Logging
Use a Single Logger Instance:
Import the logger from logger.py (backend/utils/logger.py) in all modules
Use one instance for all app.
Use appropriate log levels (DEBUG, INFO, WARNING, ERROR) based on context
Include relevant information in log messages (function name, parameters, IDs)

2. Exception Handling
Robust Error Handling:
Use specific exception types when possible
Implement proper error context and recovery mechanisms
Ensure exceptions are logged before handling

3. Data Models with Pydantic
Define Input and Output Models:
Store models in models/data_models.py
Use type hints and validation rules
Include descriptive field documentation

4. Single Responsibility Principle
Keep Functions Focused:
Each function should do exactly one thing
Limit function length (aim for under 100 lines)
Use descriptive function names that indicate purpose

5. Configuration Management
Centralize Configurations:
Store configurations in config.yaml (backend/config/config.yaml)
Access via config.py for typed access (backend/config/config.py)


6. Documentation
Document Your Functions:
Add docstrings to all functions using a consistent format
Document parameters, return types, exceptions, and examples
Keep documentation updated when code changes

7. Test
All functions should have test case
Test Coverage should be over %70 

8. Hardcoded Variables
Avoid Hardcoded Values:
- Store all configuration values in config.yaml
- Access variables through config.py
- This includes:
    - Database connections
    - API endpoints
    - Timeouts
    - Environment-specific values
    - Feature flags
