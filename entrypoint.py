#!/usr/bin/env python3
"""Custom Docling MCP entrypoint that uses a VLM pipeline (API-based).

Instead of running heavy layout analysis, OCR, and table structure models
on the CPU, this sends page images to a vision-language model API for
conversion to markdown.  Set the DOCLING_VLM_* env vars to configure.

If DOCLING_VLM_URL is not set, falls back to the default local pipeline.

Environment variables
---------------------
DOCLING_VLM_URL       OpenAI-compatible API base URL (required for VLM mode)
DOCLING_VLM_API_KEY   Bearer token for the API (optional)
DOCLING_VLM_MODEL     Model name to request (optional)
DOCLING_VLM_PROMPT    Custom conversion prompt (optional)
DOCLING_VLM_TIMEOUT   Request timeout in seconds (default: 120)
DOCLING_VLM_CONCURRENCY  Concurrent page requests (default: 2)
DOCLING_MCP_KEEP_IMAGES  Keep page images after conversion (default: false)
"""

import functools
import logging
import os

logger = logging.getLogger("docling_entrypoint")

_DEFAULT_PROMPT = (
    "Convert this document page to markdown. "
    "Faithfully reproduce all text content, preserving headings, "
    "bullet/numbered lists, tables, bold/italic formatting, and "
    "any code blocks. Do not add commentary or descriptions."
)


def patch_converter():
    """Replace the default PDF/image converter with a VLM API-based one."""
    api_base = os.environ.get("DOCLING_VLM_URL", "")
    api_key = os.environ.get("DOCLING_VLM_API_KEY", "")
    model = os.environ.get("DOCLING_VLM_MODEL", "")

    if not api_base:
        logger.info("DOCLING_VLM_URL not set — using default local pipeline")
        return

    # ── lazy imports (heavy) ──────────────────────────────────────────
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import VlmPipelineOptions
    from docling.datamodel.pipeline_options_vlm_model import (
        ApiVlmOptions,
        ResponseFormat,
    )
    from docling.document_converter import DocumentConverter, PdfFormatOption

    keep_images = (
        os.environ.get("DOCLING_MCP_KEEP_IMAGES", "false").lower() == "true"
    )
    prompt = os.environ.get("DOCLING_VLM_PROMPT", _DEFAULT_PROMPT)
    timeout = float(os.environ.get("DOCLING_VLM_TIMEOUT", "120"))
    concurrency = int(os.environ.get("DOCLING_VLM_CONCURRENCY", "2"))

    # Build the chat-completions URL
    url = api_base.rstrip("/")
    if not url.endswith("/chat/completions"):
        url += "/chat/completions"

    vlm_options = ApiVlmOptions(
        url=url,
        headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
        params={"model": model} if model else {},
        response_format=ResponseFormat.MARKDOWN,
        prompt=prompt,
        timeout=timeout,
        concurrency=concurrency,
    )

    pipeline_options = VlmPipelineOptions(
        vlm_options=vlm_options,
        generate_page_images=keep_images,
    )

    format_options = {
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
        InputFormat.IMAGE: PdfFormatOption(pipeline_options=pipeline_options),
    }

    converter = DocumentConverter(format_options=format_options)

    # Monkey-patch the cached getter in conversion module
    import docling_mcp.tools.conversion as conv

    conv._get_converter = functools.lru_cache(lambda: converter)

    logger.info("VLM pipeline active: model=%s  url=%s", model, api_base)


# ── Force the conversion module to load, then patch it ────────────
import docling_mcp.tools.conversion  # noqa: E402, F401

patch_converter()

# ── Disable DNS rebinding protection (internal Docker networking) ─
from docling_mcp.shared import mcp as _mcp  # noqa: E402

if _mcp.settings.transport_security is not None:
    _mcp.settings.transport_security.enable_dns_rebinding_protection = False

# ── Hand off to the normal CLI entrypoint ─────────────────────────
from docling_mcp.servers.mcp_server import app  # noqa: E402

app()
