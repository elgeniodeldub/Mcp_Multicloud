# Update this digest only after reviewing the official Python image release and Trivy scan.
FROM python:3.12-alpine@sha256:6d43704baacd1bfbe7c295d7f13079d5d8104ed33568873133f8fc69980419df AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apk add --no-cache build-base

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install --no-cache-dir "pip==26.2.1" "build==1.5.0" "hatchling==1.31.0" \
    && python -m build --wheel --outdir /dist

FROM python:3.12-alpine@sha256:6d43704baacd1bfbe7c295d7f13079d5d8104ed33568873133f8fc69980419df AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# gcompat/libstdc++/icu-libs let the glibc-built Azure MCP binary run on musl.
RUN apk add --no-cache nodejs npm curl gcompat libstdc++ icu-libs

# Preinstall the pinned Azure MCP server at build time instead of letting `npx -y`
# download it on every start. npm verifies each tarball against the registry's
# sha512 integrity; bump AZURE_MCP_VERSION together with config.yaml.
ARG AZURE_MCP_VERSION=2.0.4
ENV NPM_CONFIG_UPDATE_NOTIFIER=false     NPM_CONFIG_FUND=false     PATH="/opt/azure-mcp/node_modules/.bin:${PATH}"
RUN mkdir -p /opt/azure-mcp     && npm install --prefix /opt/azure-mcp --no-audit --omit=dev         "@azure/mcp@${AZURE_MCP_VERSION}"     && npm cache clean --force     && azmcp --version

COPY --from=builder /dist/*.whl /tmp/
RUN python -m pip install /tmp/*.whl \
    && rm -f /tmp/*.whl

COPY docker/config.container.yaml /etc/multicloud-mcp/config.yaml

RUN adduser -D -u 1000 mcp \
    && chown -R mcp:mcp /app
USER mcp

ENV MULTICLOUD_TRANSPORT=stdio

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["sh", "-c", "if [ \"$MULTICLOUD_TRANSPORT\" = \"http\" ]; then curl -fsS http://127.0.0.1:8080/health || exit 1; else exit 0; fi"]

ENTRYPOINT ["multicloud-mcp-server"]
CMD ["--transport", "stdio"]
