
📘 Refactored Backend Architecture Documentation
🔧 Tech Stack
Language: Python
Framework: FastAPI
Real-Time Layer: WebSockets (FastAPI WebSocket routes)
Database: SQLite (can be replaced with PostgreSQL, etc.)
Agent Framework: LangChain (via langchain_core)
Frontend: (Separate) React / JS with components like DatabaseStructure.js
📂 Project Structure (Updated)

sql_matic2/
├── main.py                          # FastAPI app & websocket router
├── api/
│   └── routes.py                    # REST API routes
├── core_logic/
│   └── chat_handler.py              # Domain layer logic
├── services/
│   ├── agent_service.py
│   ├── thread_service.py
│   ├── memory_service.py
│   └── db_service.py
├── models/
│   ├── request_models.py            # Pydantic schemas
│   └── data_models.py               # SQLAlchemy models
├── tools/
│       ├── sqlite_execute_query.py  # Runs raw SQL queries
│       ├── sqlite_get_schema.py     # Fetches DB structure
|       └── sqlite_get_metadata      # Fetches Metadata from DB
├── websocket/
│   └── handlers.py                  # WebSocket event handlers
├── events/
│   └── types.py                     # Custom event names like `database_update`
└── README.md


🧠 Core Layers Overview
 ┌────────────┐
 │   FastAPI  │     <- REST API + WebSocket Server
 └────┬───────┘
      │
 ┌────▼────────────┐
 │   Core Logic    │     <- Domain Layer
 └────┬────────────┘
      │
 ┌────▼───────────────────────────────────────────────┐
 │                    Services                        │
 │ ┌────────────┐  ┌────────────┐  ┌───────────────┐  │
 │ │AgentService│  │ThreadService│  │MemoryService │  │
 │ └────┬───────┘  └────┬───────┘  └────┬──────────┘  │
 │      │               │               │             │
 │  ┌───▼───────────────▼───────────────▼─────────┐   │
 │  │                DBService                    │   │
 │  └─────────────────────────────────────────────┘   │
 └────────────────────────────────────────────────────┘
 
 ┌─────────────┐       ┌──────────────┐
 │   Models    │       │   WebSocket  │     <- Real-time comm
 └─────────────┘       └──────────────┘

         ▲
         │
     ┌───────┐
     │ Tools │   <- Used by AgentService
     └───────┘
Services Summary
AgentService
Manages per-user agent instances
Assigns toolset (like SQLite query executor)

Uses LangChain agents
from langchain_core.tools import Tool 

ThreadService
Manages chat threads
Saves/loads messages from DB

MemoryService
Provides memory state to agents
Handles history loading and summarization

DBService
Manages all DB sessions
Invoked by tools and services

🧰 Tools
tools/sqlite/execute_query.py
tools/sqlite/get_db_schema.py
These tools are used by agents only (not shared globally), and can be customized per-agent.

🔌 WebSocket Architecture
Purpose:
Handles real-time communication between frontend and backend for:

Live thread updates
Database schema push (database_update)
Metrics & system stats
Key Events:
database_update ← triggered after get_db_schema runs
message_stream ← for real-time chat updates
thread_created ← notifies UI about new threads
metrics_update ← optional metrics stream

Event Flow Example:
User opens database view
Frontend subscribes via WebSocket to database_update
tools/sqlite/get_db_schema.py is called
Backend sends schema to client via database_update


# websocket/handlers.py
async def push_database_update(socket, db_path):
    schema = get_schema(db_path)
    await socket.send_json({"event": "database_update", "payload": schema})
🧾 REST API Documentation
Endpoint	Method	Description
/chat	POST	Handles user input to the agent
/api/threads	GET	Lists all available threads
/api/threads	POST	Creates a new chat thread
/api/database/structure	GET	Returns current DB schema
/api/metrics	GET	Returns system or chat-level metrics


📊 Logging Architecture
The application implements a structured and centralized logging system using Python’s built-in logging module with custom configuration logic.

✅ Logger Components
Root Logger: Defined in utils/logger.py, sets up both console and file handlers.
Named Loggers: Each module gets its own logger instance via get_logger(__name__), making log origin tracking easier.
Log Rotation: Enabled using RotatingFileHandler to manage file size and avoid unbounded growth of log files.

📍 Integration Points
Services Layer: Logs key lifecycle events like service startup, shutdown, and DB calls.
API Layer: Logs incoming API requests, validation errors, and responses.
WebSocket Layer: Tracks connection lifecycle, message broadcasting, and disconnections.
Agent Execution: Logs tool invocations, chain responses, and decision-making traces.


⚙️ Configuration Management
The application uses a YAML-based centralized configuration system for managing settings across all layers of the backend.

✅ Configuration System Design
Singleton Access: The config is loaded once at startup and reused everywhere.
Environment Awareness: Reads ENV variable to switch between profiles like development or production.
Override Support: Values in the YAML config can be overridden by environment variables at runtime.

🔑 Configuration Categories
Area	Description
logging	Log level, format, file path, rotation file size, etc.
agent	LLM provider, temperature, system prompts, etc.
database	Connection URI, schema file path, SQLite settings
api	WebSocket buffer size, allowed origins, rate limiting
tools	Tool-specific configuration like timeout, API keys, etc.
📂 File Path


backend/config/config.yaml
backend/config/config.py
🧪 Usage Pattern
Access with default fallback:
from config.config import config

log_level = config.get("logging", "level", default="INFO")
Access entire section:

agent_config = config.get_section("agent")
model_type = agent_config.get("model")


🔗 Frontend Integration
Component: DatabaseStructure.js
Listens for database_update WebSocket event
Triggers update when user connects to a DB or changes schema
Schema is retrieved from: tools/sqlite/get_db_schema.py
WebSocket handler ensures real-time updates without polling

🧪 Future Improvements
Add unit tests for WebSocket handlers
Tool registry for dynamically assigning tools to agents
Optional: persist agent state across restarts