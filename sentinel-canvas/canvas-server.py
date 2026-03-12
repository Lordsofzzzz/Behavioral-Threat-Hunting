#!/usr/bin/env python3
"""
Sentinel Canvas Server v2
Serves the Sentinel Canvas dashboard builder.
All data fetching happens in the browser — this server only serves static files.
"""

import os
import sys
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

HOST = 'localhost'
PORT = 8889

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.css':  'text/css; charset=utf-8',
    '.js':   'application/javascript; charset=utf-8',
    '.json': 'application/json',
    '.ico':  'image/x-icon',
    '.png':  'image/png',
    '.svg':  'image/svg+xml',
}

ALLOWED_EXTENSIONS = set(MIME_TYPES.keys())


class CanvasHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Normalise path
        path = self.path.split('?')[0]  # strip query string
        if path == '/' or path == '/index.html':
            self._serve_file(BASE_DIR / 'index.html')
        else:
            # Resolve relative to BASE_DIR, prevent path traversal
            try:
                target = (BASE_DIR / path.lstrip('/')).resolve()
                if not str(target).startswith(str(BASE_DIR.resolve())):
                    self._send_403()
                    return
                if target.suffix not in ALLOWED_EXTENSIONS:
                    self._send_404()
                    return
                self._serve_file(target)
            except Exception:
                self._send_404()

    def _serve_file(self, path: Path):
        if not path.exists() or not path.is_file():
            self._send_404()
            return
        content_type = MIME_TYPES.get(path.suffix, 'application/octet-stream')
        try:
            content = path.read_bytes()
        except OSError:
            self._send_404()
            return
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(content)

    def _send_404(self):
        self.send_response(404)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Not found')

    def _send_403(self):
        self.send_response(403)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Forbidden')

    def log_message(self, format, *args):
        pass  # suppress per-request logs


if __name__ == '__main__':
    server = HTTPServer((HOST, PORT), CanvasHandler)
    print(f'\n  ⬡ Sentinel Canvas v2  →  http://{HOST}:{PORT}')
    print(f'  Make sure Log Sentinel API is running at http://localhost:8888')
    print(f'  Press Ctrl+C to stop.\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n  Sentinel Canvas stopped.')
        sys.exit(0)
