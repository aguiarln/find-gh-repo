import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from github_repo_search.cli import main as cli_main


def load_query_from_markdown(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    content = content.strip()
    if not content:
        raise ValueError(f"The file {path} is empty.")

    content = content.strip('"').strip("'")
    content = re.sub(r"^#+\s*", "", content, flags=re.MULTILINE)
    content = re.sub(r"`([^`]*)`", r"\1", content)
    content = re.sub(r"^>\s*", "", content, flags=re.MULTILINE)
    content = " ".join(line.strip() for line in content.splitlines() if line.strip())
    return content


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read a markdown request and search GitHub repositories")
    parser.add_argument("--input", default="search_request.md", help="Path to the markdown file with the natural-language request")
    parser.add_argument("--language", help="Optional language filter")
    parser.add_argument("--topic", help="Optional topic filter")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of repositories to request")
    parser.add_argument("--demo", action="store_true", help="Use demo data instead of trying the live MCP server")
    parser.add_argument("--output", default="results.json", help="Path to save the results as JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = (PROJECT_ROOT / input_path).resolve()

    query = load_query_from_markdown(input_path)
    print(f"Using request from {input_path}")
    print(f"Query: {query}")

    cli_args = ["--query", query]
    if args.language:
        cli_args.extend(["--language", args.language])
    if args.topic:
        cli_args.extend(["--topic", args.topic])
    if args.limit:
        cli_args.extend(["--limit", str(args.limit)])
    if args.demo:
        cli_args.append("--demo")
    if args.output:
        cli_args.extend(["--output", args.output])

    return cli_main(cli_args)


if __name__ == "__main__":
    raise SystemExit(main())
