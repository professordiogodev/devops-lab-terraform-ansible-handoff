#!/usr/bin/env python3
"""A very small status service for the app server. PROVIDED, do not change.
Serves the file /opt/pollie/status.json (rendered by Ansible) on port 8000 at /status."""
from http.server import BaseHTTPRequestHandler, HTTPServer

PATH = "/opt/pollie/status.json"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/status":
            self.send_response(404)
            self.end_headers()
            return
        try:
            body = open(PATH, "rb").read()
        except OSError:
            self.send_response(503)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
