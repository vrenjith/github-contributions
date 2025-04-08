# GitHub Contributions Analyzer

A Python-based tool to analyze and visualize GitHub contributions across repositories. This tool supports both public GitHub and GitHub Enterprise instances.

## Features

- Fetch contributions from GitHub repositories
- Support for both GitHub.com and GitHub Enterprise
- Customizable date range for analysis
- Virtual environment setup included

## Prerequisites

- Python 3.x
- GitHub Personal Access Token
- Git

## Setup

1. Clone the repository:
    ```bash
    git clone <repository-url>
    cd github-contributions
    ```

2. Configure environment variables in `run_analysis.sh`:
    - `GITHUB_TOKEN`: Your GitHub personal access token
    - `GITHUB_USERNAME`: Your GitHub username
    - `GITHUB_ENTERPRISE_URL`: Your GitHub Enterprise URL (if applicable)
    - `GITHUB_IS_ENTERPRISE`: Set to "true" for GitHub Enterprise, "false" for GitHub.com
    - `START_DATE`: Analysis start date (YYYY-MM-DD)
    - `END_DATE`: Analysis end date (YYYY-MM-DD)

3. Make the script executable:
    ```bash
    chmod +x run_analysis.sh
    ```

4. Run the analysis:
    ```bash
    ./run_analysis.sh
    ```

## Usage

The script will automatically:
- Set up a Python virtual environment
- Install required dependencies
- Run the analysis based on your configuration

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.