# Update this digest only after reviewing the official Python image release and Trivy scan.
FROM python:3.14-alpine@sha256:a1321512d6a287428c50dcdf2ab3857761127e03a23b1f648e9c1c0de59288f8 AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apk add --no-cache build-base

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install --no-cache-dir "pip==26.2.1" "build==1.5.0" "hatchling==1.31.0" \
    && python -m build --wheel --outdir /dist

FROM python:3.14-alpine@sha256:a1321512d6a287428c50dcdf2ab3857761127e03a23b1f648e9c1c0de59288f8 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apk add --no-cache nodejs npm curl

COPY --from=builder /dist/*.whl /tmp/
RUN python -m pip install /tmp/*.whl \
    && rm -f /tmp/*.whl

RUN adduser -D -u 1000 mcp \
    && chown -R mcp:mcp /app
USER mcp

ENV MULTICLOUD_TRANSPORT=stdio

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["sh", "-c", "if [ \"$MULTICLOUD_TRANSPORT\" = \"http\" ]; then curl -fsS http://127.0.0.1:8080/health || exit 1; else exit 0; fi"]

ENTRYPOINT ["multicloud-mcp-server"]
CMD ["--transport", "stdio"]
