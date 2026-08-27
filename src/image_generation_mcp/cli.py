"""Command line entrypoint."""

import argparse
import logging
import sys

from .config import load_config
from .server import mcp


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="image-generation-mcp")
    parser.add_argument(
        "--transport",
        choices=("stdio", "http"),
        default=None,
        help="Transport to serve on; overrides MCP_TRANSPORT (default: stdio).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port for the http transport; overrides MCP_PORT (default: 8000).",
    )
    return parser.parse_args()


def main() -> None:
    """Run the MCP server on the selected transport."""
    # stdout carries the stdio transport's JSON-RPC frames, so logs go to stderr.
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    args = _parse_args()
    config = load_config()
    transport = args.transport or config.transport
    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(
            transport="streamable-http",
            host="127.0.0.1",
            port=args.port or config.port,
        )
