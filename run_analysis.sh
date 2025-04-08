#!/bin/bash

# Set environment variables
export GITHUB_TOKEN="***REMOVED***"
export GITHUB_USERNAME="i306570"
export GITHUB_ENTERPRISE_URL="https://github.wdf.sap.corp"
export GITHUB_IS_ENTERPRISE="true"  # Set to "true" if using GitHub Enterprise
export GITHUB_START_DATE="2025-01-01"
export GITHUB_END_DATE="2025-03-28"
export GITHUB_VERIFY_SSL=False


# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Created new virtual environment"
fi

# Activate virtual environment
source venv/bin/activate

# Install required packages
pip install --upgrade pip
pip install requests

# Run the analysis script
python analyse.py

# Deactivate virtual environment
deactivate