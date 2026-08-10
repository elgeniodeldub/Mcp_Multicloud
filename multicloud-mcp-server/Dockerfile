# Update this digest only after reviewing the official Python image release and Trivy scan.
FROM python:3.12-slim-bookworm@sha256:d50fb7611f86d04a3b0471b46d7557818d88983fc3136726336b2a4c657aa30b AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install --no-cache-dir "pip==26.2.1" "build==1.5.0" "hatchling==1.31.0" \
    && python -m build --wheel --outdir /dist

FROM python:3.12-slim-bookworm@sha256:d50fb7611f86d04a3b0471b46d7557818d88983fc3136726336b2a4c657aa30b AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs npm curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /dist/*.whl /tmp/
RUN python -m pip install /tmp/*.whl \
    && rm -f /tmp/*.whl

RUN useradd --create-home --uid 1000 mcp \
    && chown -R mcp:mcp /app
USER mcp

ENV MULTICLOUD_TRANSPORT=stdio

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD-SHELL if [ "$MULTICLOUD_TRANSPORT" = "http" ]; then curl -fsS http://127.0.0.1:8080/health || exit 1; else exit 0; fi

ENTRYPOINT ["multicloud-mcp-server"]
CMD ["--transport", "stdio"]
