#!/usr/bin/env python3
"""Serve the generated website on the first available local port."""

import argparse
import http.server
import socket
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def available_port(start_port):
    for port in range(start_port, start_port + 100):
        with socket.socket() as connection:
            if connection.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError(f"No available port from {start_port} to {start_port + 99}")


def main():
    parser = argparse.ArgumentParser(description="Serve the generated website locally")
    parser.add_argument("--directory", type=Path, default=ROOT / "_site")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    port = available_port(args.port)
    handler = lambda *handler_args, **handler_kwargs: http.server.SimpleHTTPRequestHandler(
        *handler_args, directory=args.directory, **handler_kwargs
    )
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print(f"Serving {args.directory.resolve()} at http://127.0.0.1:{port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nPreview server stopped")


if __name__ == "__main__":
    main()
