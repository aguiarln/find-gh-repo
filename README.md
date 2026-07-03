# GitHub MCP Repository Search

This mini-project helps you describe the kind of repository you want to find in [search_request.md](search_request.md), then run the Python script to search GitHub repositories.

## How to use it

1. Open [search_request.md](search_request.md) and write what you want to find.
2. From the project root, run:
   ```bash
   python search_from_markdown.py
   ```
3. The script reads your request from [search_request.md](search_request.md), runs the repository search, and saves the results to [results.json](results.json).

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Optional arguments

You can add filters or change the output file when running the script:

- `--language "python"` to filter by language
- `--topic "ai"` to filter by topic
- `--limit 10` to change the number of results
- `--demo` to use demo data instead of trying the live MCP server
- `--output my_results.json` to save results to a different file
