# docling

Prebuilt [docling-mcp](https://github.com/docling-project/docling-mcp) Docker image with **VLM API pipeline** support.

Instead of running heavy local layout analysis / OCR / table structure models on the CPU, this image can optionally route document conversion through an OpenAI-compatible vision-language model API.

## Usage

```yaml
# docker-compose.yml
services:
  docling:
    image: ghcr.io/izykitten/docling:latest
    environment:
      # VLM mode (omit these to use the default local pipeline)
      - DOCLING_VLM_URL=https://generativelanguage.googleapis.com/v1beta/openai
      - DOCLING_VLM_API_KEY=AIza...
      - DOCLING_VLM_MODEL=gemini-3-flash-preview
      # Optional
      - DOCLING_MCP_KEEP_IMAGES=true
    ports:
      - "8000:8000"
```

Or standalone:

```bash
docker run -p 8000:8000 \
  -e DOCLING_VLM_URL=https://generativelanguage.googleapis.com/v1beta/openai \
  -e DOCLING_VLM_API_KEY=AIza... \
  -e DOCLING_VLM_MODEL=gemini-3-flash-preview \
  ghcr.io/izykitten/docling:latest
```

The MCP server is available at `http://localhost:8000/mcp` (streamable-http transport).

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DOCLING_VLM_URL` | No* | — | OpenAI-compatible API base URL. Enables VLM mode. |
| `DOCLING_VLM_API_KEY` | No | — | Bearer token for the VLM API |
| `DOCLING_VLM_MODEL` | No | — | Model name to request |
| `DOCLING_VLM_PROMPT` | No | (built-in) | Custom system prompt for page conversion |
| `DOCLING_VLM_TIMEOUT` | No | `120` | Per-page request timeout (seconds) |
| `DOCLING_VLM_CONCURRENCY` | No | `2` | Max concurrent page conversion requests |
| `DOCLING_MCP_KEEP_IMAGES` | No | `false` | Retain page images after conversion |

\* If `DOCLING_VLM_URL` is not set, falls back to the default docling local pipeline (CPU-based layout analysis + OCR).

## How it works

The entrypoint monkey-patches `docling-mcp`'s default `DocumentConverter` factory to use a [`VlmPipelineOptions`](https://docling-project.github.io/docling/usage/vlm/) with [`ApiVlmOptions`](https://docling-project.github.io/docling/usage/vlm/#using-apis) when `DOCLING_VLM_URL` is set. This is needed because upstream `docling-mcp` doesn't expose VLM pipeline configuration through its CLI or environment variables.

DNS rebinding protection is also disabled for Docker networking compatibility.

## Build schedule

The image is rebuilt **weekly** (Mondays 06:00 UTC) to pick up new `docling-mcp` releases, and on every push to `main`.

## License

MIT — same as [docling-mcp](https://github.com/docling-project/docling-mcp).
