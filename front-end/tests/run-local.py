"""Build first, then run browser regressions with disposable local data only."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[2]
assets = root / 'front-end/dist/serve-front-end/browser'
if not (assets / 'index.html').exists():
    raise SystemExit('Run npm run build first.')

with tempfile.TemporaryDirectory(prefix='serve-regression-') as scratch:
    env = dict(os.environ, DEBUG='False', SECURE_SSL_REDIRECT='False', DJANGO_SETTINGS_MODULE='config.test_settings', TEST_DATABASE_NAME=str(Path(scratch) / 'db.sqlite3'),
               TEST_MEDIA_ROOT=str(Path(scratch) / 'media'), E2E_USERNAME='local-regression-admin',
               E2E_PASSWORD=secrets.token_urlsafe(24))
    if not env.get('E2E_IMAGE'):
        from PIL import Image
        image = Image.open(root / 'front-end/src/assets/hero-joao-pessoa.jpg')
        image.thumbnail((800, 600))
        fixture = Path(scratch) / 'fixture.jpg'
        image.save(fixture, quality=85)
        env['E2E_IMAGE'] = str(fixture)
    manage = [sys.executable, 'manage.py']
    subprocess.run(manage + ['migrate', '--settings=config.test_settings', '--noinput'], cwd=root / 'back-end', env=env, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(manage + ['shell', '--settings=config.test_settings', '-c',
        "import os; from django.contrib.auth import get_user_model; u=get_user_model().objects.create_user(username=os.environ['E2E_USERNAME'],password=os.environ['E2E_PASSWORD'],is_staff=True)"],
        cwd=root / 'back-end', env=env, check=True, stdout=subprocess.DEVNULL)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        api_port = sock.getsockname()[1]

    class Handler(SimpleHTTPRequestHandler):
        def proxy(self):
            size = int(self.headers.get('Content-Length', 0))
            headers = {key: value for key, value in self.headers.items() if key.lower() not in ('host', 'connection', 'accept-encoding')}
            request = Request(f'http://127.0.0.1:{api_port}{self.path}', data=self.rfile.read(size) if size else None,
                              headers=headers, method=self.command)
            try:
                response = urlopen(request, timeout=30)
            except HTTPError as error:
                response = error
            with response:
                self.send_response(response.status)
                for key, value in response.headers.items():
                    if key.lower() not in ('transfer-encoding', 'connection', 'content-length'):
                        self.send_header(key, value)
                body = response.read()
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass  # Browser navigation can cancel an in-flight request.

        def do_GET(self):
            if self.path.startswith(('/api/', '/media/')):
                return self.proxy()
            if not (assets / self.path.split('?')[0].lstrip('/')).is_file():
                self.path = '/index.html'
            return super().do_GET()

        def do_POST(self): self.proxy()
        def do_PATCH(self): self.proxy()
        def do_PUT(self): self.proxy()
        def do_DELETE(self): self.proxy()
        def log_message(self, *_): pass

    with open(Path(scratch) / 'api.log', 'w') as log:
        api = subprocess.Popen([sys.executable, '-m', 'gunicorn', 'config.wsgi:application', '--bind', f'127.0.0.1:{api_port}', '--workers', '1', '--threads', '2'],
                               cwd=root / 'back-end', env=env, stdout=log, stderr=log)
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(assets)))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for _ in range(100):
                try:
                    urlopen(f'http://127.0.0.1:{api_port}/api/', timeout=1).close()
                    break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError('Local API did not start.')
            env['E2E_BASE_URL'] = f'http://127.0.0.1:{server.server_port}'
            subprocess.run(['node', 'tests/browser-regression.mjs'], cwd=root / 'front-end', env=env, check=True)
        finally:
            api.terminate()
            api.wait(timeout=10)
            server.shutdown()
            server.server_close()
            thread.join()
