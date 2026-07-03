import argparse
import asyncio
import json
import os
import sys
from typing import Any, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def build_search_query(base_query: str, language: str | None = None, topic: str | None = None) -> str:
    parts = [base_query.strip()]
    if language:
        parts.append(f"language:{language.strip()}")
    if topic:
        parts.append(f"topic:{topic.strip()}")
    return " ".join(parts)


def normalize_repos(raw_items: Sequence[dict[str, Any]] | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in raw_items or []:
        if isinstance(item, str):
            normalized.append(
                {
                    "name": item,
                    "full_name": item,
                    "html_url": "",
                    "description": "",
                    "stars": 0,
                }
            )
            continue

        repo = item or {}
        normalized.append(
            {
                "name": repo.get("name") or repo.get("full_name") or "",
                "full_name": repo.get("full_name") or repo.get("name") or "",
                "html_url": repo.get("html_url") or repo.get("url") or "",
                "description": repo.get("description") or "",
                "stars": repo.get("stargazers_count") or repo.get("stars") or 0,
            }
        )
    return normalized


class RepoSearchError(RuntimeError):
    """Raised when the MCP search flow cannot return usable repository data."""


async def search_via_mcp(query: str, limit: int = 5, server_command: str | None = None, server_args: str | None = None) -> list[dict[str, Any]]:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    command = server_command or os.environ.get("GITHUB_MCP_COMMAND", "npx")
    args = server_args or os.environ.get("GITHUB_MCP_ARGS", "-y @modelcontextprotocol/server-github")
    server_args_list = [token for token in args.split() if token]

    server_params = StdioServerParameters(
        command=command,
        args=server_args_list,
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            tool_names = [tool.name for tool in getattr(tools_result, "tools", [])]

            if not tool_names:
                raise RepoSearchError("The MCP server did not expose any tools.")

            search_tool = next(
                (name for name in tool_names if "repo" in name.lower() and "search" in name.lower()),
                None,
            )
            if search_tool is None:
                search_tool = next((name for name in tool_names if "search" in name.lower()), None)

            if search_tool is None:
                raise RepoSearchError(f"No suitable repository search tool found. Available tools: {tool_names}")

            candidate_payloads = [
                {"query": query, "limit": limit},
                {"query": query, "per_page": limit},
                {"query": query},
                {"query": query, "pageSize": limit},
            ]

            last_error: Exception | None = None
            for payload in candidate_payloads:
                try:
                    result = await session.call_tool(search_tool, payload)
                    return extract_repositories(result)
                except Exception as exc:  # pragma: no cover - depends on MCP server behaviour
                    last_error = exc

            if last_error is not None:
                raise RepoSearchError(str(last_error)) from last_error
            raise RepoSearchError("The MCP tool did not return repository results.")


def extract_repositories(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, dict):
        if isinstance(result.get("repositories"), list):
            return result["repositories"]
        if isinstance(result.get("items"), list):
            return result["items"]
        if isinstance(result.get("data"), list):
            return result["data"]
        if isinstance(result.get("results"), list):
            return result["results"]

    content = getattr(result, "content", None)
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
            elif hasattr(item, "text"):
                text_parts.append(getattr(item, "text"))
        text = "\n".join(part for part in text_parts if part)
        if text:
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                return []

            if isinstance(payload, dict):
                if isinstance(payload.get("repositories"), list):
                    return payload["repositories"]
                if isinstance(payload.get("items"), list):
                    return payload["items"]
                if isinstance(payload.get("data"), list):
                    return payload["data"]
                if isinstance(payload.get("results"), list):
                    return payload["results"]
            elif isinstance(payload, list):
                return payload

    return []


def repo_url_exists(url: str | None, timeout: int = 15) -> bool:
    if not url:
        return False

    try:
        request = Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=timeout) as response:
            return response.status < 400
    except HTTPError as exc:
        if exc.code in {403, 405}:
            try:
                request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urlopen(request, timeout=timeout) as response:
                    return response.status < 400
            except Exception:
                return False
        return False
    except (URLError, TimeoutError, ValueError):
        return False


def filter_existing_repositories(repos: Sequence[dict[str, Any]] | None, checker: Any = None) -> list[dict[str, Any]]:
    checker = checker or repo_url_exists
    filtered: list[dict[str, Any]] = []

    for repo in repos or []:
        if not isinstance(repo, dict):
            continue

        html_url = repo.get("html_url") or repo.get("url") or ""
        if not html_url and repo.get("full_name"):
            html_url = f"https://github.com/{repo['full_name']}"

        if html_url and checker(html_url):
            filtered.append(repo)

    return filtered


def build_demo_repositories(query: str) -> list[dict[str, Any]]:
    return [
        {
            "name": "FlightTicketMCP",
            "full_name": "xiaonieli7/FlightTicketMCP",
            "html_url": "https://github.com/xiaonieli7/FlightTicketMCP",
            "description": f"Demo repository about {query}",
            "stargazers_count": 43,
        },
        {
            "name": "findtrip",
            "full_name": "fankcoder/findtrip",
            "html_url": "https://github.com/fankcoder/findtrip",
            "description": f"Another sample match for {query}",
            "stargazers_count": 486,
        },
        {
            "name": "flight-scraper",
            "full_name": "yang/flight-scraper",
            "html_url": "https://github.com/yang/flight-scraper",
            "description": f"A sample flight-related repository for {query}",
            "stargazers_count": 32,
        },
    ]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search GitHub repositories via an MCP server")
    parser.add_argument("--query", required=True, help="Search query, for example: fastapi auth")
    parser.add_argument("--language", help="Optional language filter")
    parser.add_argument("--topic", help="Optional topic filter")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of items to request")
    parser.add_argument("--demo", action="store_true", help="Use built-in demo data instead of a live MCP server")
    parser.add_argument("--server-command", help="Command used to start the MCP server")
    parser.add_argument("--server-args", help="Arguments passed to the MCP server command")
    parser.add_argument("--output", help="Optional path to save the results as JSON")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    query = build_search_query(args.query, language=args.language, topic=args.topic)

    if args.demo:
        repos = build_demo_repositories(query)
    else:
        try:
            repos = asyncio.run(
                search_via_mcp(
                    query,
                    limit=args.limit,
                    server_command=args.server_command,
                    server_args=args.server_args,
                )
            )
        except Exception as exc:
            print(f"Warning: unable to reach the MCP server ({exc}). Falling back to demo data.", file=sys.stderr)
            repos = build_demo_repositories(query)

    repos = filter_existing_repositories(repos)
    normalized = normalize_repos(repos)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(normalized, handle, indent=2)
        print(f"Wrote {len(normalized)} results to {args.output}")
    else:
        print(json.dumps(normalized, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
