"""Local HTTP server that captures OAuth / OpenID callback redirects."""

import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional


_SUCCESS_HTML = b"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>body{background:#141218;color:#E6E1E5;font-family:"Segoe UI",sans-serif;
display:flex;flex-direction:column;align-items:center;justify-content:center;
height:100vh;margin:0;}h2{color:#EADDFF;}p{color:#938F99;}</style></head>
<body><h2>Autenticacion completada</h2>
<p>Podes cerrar esta ventana y volver al Game Manager.</p></body></html>"""

_WAITING_HTML = b"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>body{background:#141218;color:#938F99;font-family:"Segoe UI",sans-serif;
display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}
</style></head><body><p>Procesando...</p></body></html>"""


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server._captured = self.path
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(_SUCCESS_HTML)

    def log_message(self, *_):
        pass  # suppress console noise


def wait_for_callback(port: int, path_prefix: str,
                      timeout: int = 120) -> Optional[str]:
    """
    Start a local HTTP server on `port`, wait up to `timeout` seconds for
    a GET request whose path starts with `path_prefix`.
    Returns the full request path (including query string) or None on timeout.
    """
    server = HTTPServer(("127.0.0.1", port), _Handler)
    server._captured = None
    server.timeout = 1.0          # handle_request blocks at most 1 s per call

    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline:
            server.handle_request()
            if server._captured and server._captured.startswith(path_prefix):
                return server._captured
    finally:
        server.server_close()
    return None
