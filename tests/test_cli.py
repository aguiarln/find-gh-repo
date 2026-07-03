from github_repo_search.cli import build_search_query, normalize_repos, filter_existing_repositories


def test_build_search_query_includes_language_and_topic():
    query = build_search_query("fastapi", language="python", topic="auth")
    assert "fastapi" in query
    assert "language:python" in query
    assert "topic:auth" in query


def test_normalize_repos_converts_records_to_simple_dicts():
    raw = [
        {"name": "demo", "full_name": "octo/demo", "html_url": "https://example.com", "description": "Demo repo", "stargazers_count": 10},
    ]

    normalized = normalize_repos(raw)

    assert normalized[0]["name"] == "demo"
    assert normalized[0]["stars"] == 10


def test_filter_existing_repositories_keeps_only_valid_urls():
    repos = [
        {"name": "ok", "full_name": "octo/ok", "html_url": "https://example.com/ok", "description": "", "stargazers_count": 1},
        {"name": "bad", "full_name": "octo/bad", "html_url": "https://example.com/bad", "description": "", "stargazers_count": 2},
    ]

    filtered = filter_existing_repositories(repos, checker=lambda url: url.endswith("/ok"))

    assert [repo["name"] for repo in filtered] == ["ok"]
