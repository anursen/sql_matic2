#!/bin/bash

# Install requirements (uncomment if needed)
# pip install -r requirements.txt

# Run the FastAPI server
echo "Starting SQL Matic backend on port 8000..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
