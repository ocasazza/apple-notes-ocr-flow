#!/bin/bash
# Simple wrapper script to run the Apple Notes to Claude workflow

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Create and activate virtual environment if it doesn't exist
VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        echo "Please make sure the 'venv' module is installed."
        exit 1
    fi
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install required packages from requirements.txt
echo "Installing required packages..."
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip install -r "$SCRIPT_DIR/requirements.txt"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install required packages."
        echo "Please check the error messages above."
        deactivate
        exit 1
    fi
else
    echo "Warning: requirements.txt not found. Some packages may need to be installed manually."
fi

# Run the workflow script with all arguments passed to this script
echo "Starting Apple Notes to Claude workflow..."
python "$SCRIPT_DIR/src/workflow.py" "$@"
WORKFLOW_EXIT_CODE=$?

# Deactivate the virtual environment
deactivate

# Check if the workflow completed successfully
if [ $WORKFLOW_EXIT_CODE -eq 0 ]; then
    echo "Workflow completed successfully!"
    echo "Check the output directory for results."
else
    echo "Workflow encountered an error."
    echo "Please check the error messages above."
fi

exit $WORKFLOW_EXIT_CODE
