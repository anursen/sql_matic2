# SQL Matic Frontend Data Types

This document outlines all the data types and structures required by the SQL Matic frontend application. Use this as a reference when developing the backend to ensure compatibility between the two systems.

## Table of Contents

- [Message Data](#message-data)
- [Thread Data](#thread-data)
- [User Data](#user-data)
- [Database Structure Data](#database-structure-data)
- [Metrics Data](#metrics-data)
- [API Endpoints](#api-endpoints)

## Message Data

Messages are the core data type in the chat application.

### Message Object

```typescript
{
  text: string;             // The message content (supports markdown)
  sender: "user" | "bot";   // Who sent the message
  userId: string;           // ID of the sender (e.g., "User1", "SQL-Bot")
  timestamp: string;        // ISO 8601 timestamp
  threadId: string;         // ID of the thread this message belongs to
}
```

### Example

```json
{
  "text": "How do I create a table in SQL?",
  "sender": "user",
  "userId": "User1",
  "timestamp": "2023-08-15T14:32:45.000Z",
  "threadId": "thread-1692107565000"
}
```

## Thread Data

Threads represent conversations.

### Thread Object

```typescript
{
  id: string;               // Unique identifier (e.g., "thread-1692107565000")
  name: string;             // Display name of the thread
  messages: Message[];      // Array of messages in this thread
  lastMessageTime: string;  // ISO 8601 timestamp of the last message
}
```

### Example

```json
{
  "id": "thread-1692107565000",
  "name": "How to create tables",
  "messages": [],           // Array of message objects
  "lastMessageTime": "2023-08-15T14:32:45.000Z"
}
```

## User Data

User information displayed in the app.

### User Object

```typescript
{
  id: string;               // User identifier (e.g., "User1", "Admin")
  isAdmin: boolean;         // Whether the user has admin privileges
}
```

### Example

```json
{
  "id": "Admin",
  "isAdmin": true
}
```

## Database Structure Data

Represents the schema of databases being queried or discussed.

### Database Structure Object

```typescript
{
  databases: [
    {
      name: string;         // Database name
      tables: [
        {
          name: string;     // Table name
          columns: [
            {
              name: string; // Column name
              type: string; // SQL data type (e.g., "INT PRIMARY KEY")
            }
          ]
        }
      ]
    }
  ]
}
```

### Example

```json
{
  "databases": [
    {
      "name": "Sample Database",
      "tables": [
        {
          "name": "users",
          "columns": [
            { "name": "id", "type": "INT PRIMARY KEY" },
            { "name": "username", "type": "VARCHAR(50)" },
            { "name": "email", "type": "VARCHAR(100)" },
            { "name": "created_at", "type": "TIMESTAMP" }
          ]
        }
      ]
    }
  ]
}
```

## Metrics Data

Usage and performance metrics displayed in the UI.

### Metrics Object

```typescript
{
  tokenUsage: {
    prompt: number;         // Number of tokens in prompts
    completion: number;     // Number of tokens in completions
    total: number;          // Total tokens used
  },
  databaseStats: {
    databaseCount: number;  // Number of databases
    tableCount: number;     // Number of tables
    rowCount: number;       // Total number of rows
  },
  performance: {
    averageResponseTime: number; // Average response time in ms
    lastQueryTime: number;       // Last query time in ms
  },
  lastUpdated: string;      // ISO 8601 timestamp
}
```

### Example

```json
{
  "tokenUsage": {
    "prompt": 450,
    "completion": 230,
    "total": 680
  },
  "databaseStats": {
    "databaseCount": 1,
    "tableCount": 12,
    "rowCount": 5723
  },
  "performance": {
    "averageResponseTime": 245,
    "lastQueryTime": 178
  },
  "lastUpdated": "2023-08-15T14:45:30.000Z"
}
```

## API Endpoints

These are the expected API endpoints and their response formats.

### Chat Message API

**Endpoint**: `POST /api/chat`

**Request:**
```json
{
  "message": "How do I create a table in SQL?",
  "userId": "User1",
  "threadId": "thread-1692107565000"
}
```

**Response:**
```json
{
  "text": "To create a table in SQL, you use the CREATE TABLE statement...",
  "timestamp": "2023-08-15T14:32:50.000Z"
}
```

### Get Threads API

**Endpoint**: `GET /api/threads`

**Response:**
```json
{
  "threads": [
    {
      "id": "thread-1692107565000",
      "name": "How to create tables",
      "lastMessageTime": "2023-08-15T14:32:45.000Z"
    },
    {
      "id": "thread-1692104565000",
      "name": "SQL joins explained",
      "lastMessageTime": "2023-08-15T13:42:45.000Z"
    }
  ]
}
```

### Get Thread Messages API

**Endpoint**: `GET /api/threads/{threadId}/messages`

**Response:**
```json
{
  "messages": [
    {
      "text": "How do I create a table in SQL?",
      "sender": "user",
      "userId": "User1",
      "timestamp": "2023-08-15T14:32:45.000Z",
      "threadId": "thread-1692107565000"
    },
    {
      "text": "To create a table in SQL, you use the CREATE TABLE statement...",
      "sender": "bot",
      "userId": "SQL-Bot",
      "timestamp": "2023-08-15T14:32:50.000Z",
      "threadId": "thread-1692107565000"
    }
  ]
}
```

### Create Thread API

**Endpoint**: `POST /api/threads`

**Request:**
```json
{
  "name": "New Conversation",
  "userId": "User1"
}
```

**Response:**
```json
{
  "id": "thread-1692107890000",
  "name": "New Conversation",
  "messages": [],
  "lastMessageTime": "2023-08-15T14:38:10.000Z"
}
```

### Get Database Structure API

**Endpoint**: `GET /api/database/structure`

**Response:** Database Structure Object (as defined above)

### Get Metrics API

**Endpoint**: `GET /api/metrics`

**Response:** Metrics Object (as defined above)

## WebSocket Events

The frontend expects these WebSocket events:

### message

Emitted when a new message is received.

```json
{
  "text": "To create a table in SQL, you use the CREATE TABLE statement...",
  "sender": "bot",
  "userId": "SQL-Bot",
  "timestamp": "2023-08-15T14:32:50.000Z",
  "threadId": "thread-1692107565000"
}
```

### typing

Emitted when the bot is typing/processing a response.

```json
{
  "isTyping": true,
  "threadId": "thread-1692107565000"
}
```

### database_update

Emitted when the database structure is updated.

```json
{
  "type": "database_update",
  "data": {
    // Database Structure Object
  }
}
```

### metrics_update

Emitted when usage metrics are updated.

```json
{
  "type": "metrics_update",
  "data": {
    // Metrics Object
  }
}
```
