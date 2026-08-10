# Contributing

1. Branch from `main`.
2. Keep changes focused.
3. Add/update tests.
4. Update docs when behavior, configuration, or tool contracts change.
5. Run:

```bash
cd multicloud-mcp-server
python -m pytest
python -m ruff check .
python -m mypy --strict src
```

Do not commit cloud credentials, API keys, Bearer tokens, `.env` files, private keys, client secrets, or production secrets.

When changing MCP tools, keep names stable unless intentionally breaking, document schemas/limitations, return structured results, and distinguish actual billing data from estimates.
