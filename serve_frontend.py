from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import os
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parent / 'frontend'
HOST = os.getenv('FRONTEND_HOST', '0.0.0.0')
PORT = int(os.getenv('FRONTEND_PORT', '3000'))

class FrontendHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def log_message(self, format, *args):
        print(f"[frontend] {self.address_string()} - {format % args}")

if __name__ == '__main__':
    print(f'Serving frontend from {FRONTEND_DIR} on http://{HOST}:{PORT}')
    httpd = ThreadingHTTPServer((HOST, PORT), FrontendHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nStopping frontend server...')
    finally:
        httpd.server_close()
