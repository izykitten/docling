FROM python:3.12-slim-trixie

LABEL org.opencontainers.image.source="https://github.com/izykitten/docling"
LABEL org.opencontainers.image.description="Docling MCP server with VLM API pipeline support"
LABEL org.opencontainers.image.licenses="MIT"

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv pip install --system --compile-bytecode docling-mcp

COPY entrypoint.py /app/entrypoint.py

WORKDIR /data
EXPOSE 8000

ENTRYPOINT ["python", "/app/entrypoint.py"]
CMD ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
