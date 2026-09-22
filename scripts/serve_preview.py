#!/usr/bin/env python3
"""Serve a chosen preview directory on localhost, with media byte-range support."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
from pathlib import Path
import argparse
import re

class RangeHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        self._remaining = None
        path = Path(self.translate_path(self.path))
        request = self.headers.get('Range', '')
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', request)
        if not path.is_file() or not match or not any(match.groups()):
            return super().send_head()
        size = path.stat().st_size
        first, last = match.groups()
        if first:
            start, end = int(first), min(int(last) if last else size-1, size-1)
        else:
            length = int(last)
            start, end = max(0, size-length), size-1
        if start >= size or end < start or (not first and int(last) == 0):
            self.send_response(416)
            self.send_header('Content-Range', f'bytes */{size}')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return None
        source = path.open('rb')
        source.seek(start)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(str(path)))
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(end-start+1))
        self.end_headers()
        self._remaining = end-start+1
        return source

    def end_headers(self):
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def copyfile(self, source, outputfile):
        try:
            if self._remaining is None:
                return super().copyfile(source, outputfile)
            while self._remaining > 0:
                data = source.read(min(262144, self._remaining))
                if not data:
                    break
                outputfile.write(data)
                self._remaining -= len(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path.cwd())
    parser.add_argument('--port', type=int, default=8772)
    args = parser.parse_args()
    directory = args.directory.resolve()
    if not directory.is_dir():
        parser.error('directory must exist')
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(RangeHandler, directory=str(directory)))
    print(f'Preview: http://127.0.0.1:{server.server_port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
