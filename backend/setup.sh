#!/bin/bash

# Print colorful messages
print_blue() {
    echo -e "\033[0;34m$1\033[0m"
}

print_green() {
    echo -e "\033[0;32m$1\033[0m"
}

print_yellow() {
    echo -e "\033[0;33m$1\033[0m"
}

# Create necessary directories
print_blue "Creating necessary directories..."
mkdir -p tools
mkdir -p user_files
print_green "Directories created!"

# Check if Python 3 is installed
print_blue "Checking for Python 3..."
if ! command -v python3 &> /dev/null; then
    print_yellow "Python 3 not found. Please install Python 3 first."
    exit 1
else
    python_version=$(python3 --version)
    print_green "Found $python_version"
fi

# Check if virtual environment exists, create if it doesn't
if [ ! -d "venv" ]; then
    print_blue "Creating virtual environment..."
    python3 -m venv venv
    print_green "Virtual environment created!"
else
    print_green "Virtual environment already exists."
fi

# Activate virtual environment
print_blue "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_blue "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Make run.sh executable
chmod +x run.sh

print_green "Setup complete! You can now run the app with:"
print_yellow "source venv/bin/activate  # If not already activated"
print_yellow "./run.sh"
print_green "Or run the demo client with:"
print_yellow "python3 demo_client.py"

# Check for API keys in .env file
if [ -f ".env" ]; then
    print_blue "Checking .env file for API keys..."
    if ! grep -q "ANTHROPIC_API_KEY=" .env || grep -q "ANTHROPIC_API_KEY=your_anthropic_api_key_here" .env; then
        print_yellow "Warning: ANTHROPIC_API_KEY not set in .env file"
    fi
    if ! grep -q "TAVILY_API_KEY=" .env || grep -q "TAVILY_API_KEY=your_tavily_api_key_here" .env; then
        print_yellow "Warning: TAVILY_API_KEY not set in .env file"
    fi
else
    print_yellow "Warning: .env file not found. Make sure to create one with your API keys."
fi

print_green "To update your API keys, edit the .env file."
