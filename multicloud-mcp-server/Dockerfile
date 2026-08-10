FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

RUN apt-get update && apt-get install -y --no-install-recommends \\
    nodejs npm curl \\
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN uv pip install --system --no-cache -e "."

RUN useradd -m -u 1000 mcp && chown -R mcp:mcp /app
USER mcp

ENV MULTICLOUD_TRANSPORT=stdio
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' || exit 1

ENTRYPOINT ["multicloud-mcp-server"]
CMD ["--transport", "stdio"]
