# GitHub MCP Repository Search

This mini-project provides a simple CLI to search GitHub repositories using a GitHub MCP server.

## Quick start

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run a demo search:
   ```bash
   python -m github_repo_search.cli --query "fastapi auth" --demo
   ```
4. To use a real MCP server, provide a command that starts it:
   ```bash
   python -m github_repo_search.cli --query "python data science" --server-command "npx" --server-args "-y @modelcontextprotocol/server-github"
   ```

## Notes

- The CLI supports optional language and topic filters.
- If no MCP server is reachable, it falls back to a simple demo dataset.
