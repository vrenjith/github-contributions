#!/bin/bash

# Set environment variables
# export GITHUB_TOKEN=
# export GITHUB_USERNAME=
# export GITHUB_ENTERPRISE_URL=
# export GITHUB_IS_ENTERPRISE=
# export GITHUB_START_DATE=
# export GITHUB_END_DATE=
# export GITHUB_VERIFY_SSL=


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