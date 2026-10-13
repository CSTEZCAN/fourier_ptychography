#!/usr/bin/env python3
import argparse
import cgi
import html
import http.server
import io
import os
import socketserver
import time
import urllib.parse
from threading import Condition

import picamera


# --- Camera MJPEG Streaming Setup ---
class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b"\xff\xd8"):
            # New JPEG frame detected, swap buffer
            self.buffer.seek(0)
            self.frame = self.buffer.read()
            self.buffer.seek(0)
            self.buffer.truncate()
            with self.condition:
                self.condition.notify_all()
        return self.buffer.write(buf)


# Global output buffer and active camera reference
output = StreamingOutput()
camera = None


def init_camera():
    global camera
    if camera is None:
        camera = picamera.PiCamera(resolution="1920x1080", framerate=15)
        # Low bitrate / high compression parameters to keep bandwidth <= 500KB/s
        camera.start_recording(output, format="mjpeg", quality=25)
        time.sleep(1)  # Warm-up time


class DetailedHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Route to video stream endpoint
        if self.path == "/stream.mjpg":
            init_camera()
            self.send_response(200)
            self.send_header("Age", "0")
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header(
                "Content-Type", "multipart/x-mixed-replace; boundary=FRAME"
            )
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b"--FRAME\r\n")
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", str(len(frame)))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
            except Exception as e:
                print("Client disconnected from stream:", e)
            return

        # Fallback to normal SimpleHTTPRequestHandler routing for GET
        return super().do_GET()

    def list_directory(self, path):
        try:
            entries = os.listdir(path)
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None

        entries.sort(key=lambda a: a.lower())

        try:
            displaypath = html.escape(
                urllib.parse.unquote(self.path, errors="surrogatepass"),
                quote=False,
            )
        except TypeError:
            displaypath = html.escape(
                urllib.parse.unquote(self.path), quote=False
            )

        r = []
        r.append("<!DOCTYPE html>")
        r.append("<html><head><meta charset=\"utf-8\">")
        r.append("<title>Directory listing for {}</title>".format(displaypath))
        r.append(
            "<style>"
            "body { font-family: system-ui, -apple-system, sans-serif; margin: 20px; }"
            ".control-box { background: #e8f0fe; border: 1px solid #aecbfa; padding: 15px; border-radius: 5px; margin-bottom: 15px; }"
            ".upload-box { background: #f8f9fa; border: 1px solid #ced4da; padding: 15px; border-radius: 5px; margin-bottom: 20px; }"
            "table { border-collapse: collapse; font-family: monospace; width: 100%; margin-top: 10px; }"
            "th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid #ddd; }"
            "th { background-color: #f1f3f5; }"
            "tr:hover { background-color: #f8f9fa; }"
            "a { color: #1a73e8; text-decoration: none; }"
            "a:hover { text-decoration: underline; }"
            ".btn { display: inline-block; background: #1a73e8; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; }"
            ".btn:hover { background: #1557b0; text-decoration: none; }"
            "input[type=file] { margin-right: 10px; }"
            "input[type=submit] { background: #1a73e8; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; }"
            "input[type=submit]:hover { background: #1557b0; }"
            "</style></head>"
        )
        r.append("<body>")
        r.append("<h2>Directory listing for {}</h2>".format(displaypath))

        # Camera Stream Button Section
        r.append('<div class="control-box">')
        r.append("<strong>Raspberry Pi Live Camera:</strong><br><br>")
        r.append(
            '<a class="btn" href="/stream.mjpg" target="_blank">Open Live Stream (New Tab)</a>'
        )
        r.append("</div>")

        # Upload Form
        r.append('<div class="upload-box">')
        r.append("<strong>Send File to Raspberry Pi:</strong><br><br>")
        r.append('<form enctype="multipart/form-data" method="post">')
        r.append('<input name="file" type="file"/>')
        r.append('<input type="submit" value="Upload"/>')
        r.append("</form></div>")

        r.append("<hr><table>")
        r.append(
            "<tr><th>Name</th><th>Type</th><th>Size</th><th>Last Modified</th></tr>"
        )

        # Include parent directory link if not at root
        if self.path != "/":
            r.append(
                '<tr><td><a href="../">../</a></td><td>Directory</td><td>-</td><td>-</td></tr>'
            )

        for name in entries:
            fullname = os.path.join(path, name)
            display_name = linkname = name
            is_dir = os.path.isdir(fullname)

            if is_dir:
                display_name = name + "/"
                linkname = name + "/"
                size_str = "-"
                type_str = "Directory"
            else:
                type_str = "File"
                try:
                    size = float(os.path.getsize(fullname))
                    for unit in ["B", "KB", "MB", "GB", "TB"]:
                        if size < 1024.0:
                            size_str = "{:.1f} {}".format(size, unit)
                            break
                        size /= 1024.0
                except OSError:
                    size_str = "N/A"

            try:
                mtime = time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.localtime(os.path.getmtime(fullname)),
                )
            except OSError:
                mtime = "N/A"

            r.append(
                '<tr><td><a href="{}">{}</a></td>'.format(
                    urllib.parse.quote(linkname), html.escape(display_name)
                )
            )
            r.append(
                "<td>{}</td><td>{}</td><td>{}</td></tr>".format(
                    type_str, size_str, mtime
                )
            )

        r.append("</table><hr></body></html>")

        try:
            encoded = "\n".join(r).encode("utf-8", "surrogateescape")
        except Exception:
            encoded = "\n".join(r).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
        return None

    def do_POST(self):
        """Handle file uploads via multipart HTTP POST request."""
        r, info = self.deal_post_data()
        print(r, info, "by", self.client_address)

        f = []
        f.append("<!DOCTYPE html><html><head><meta charset=\"utf-8\">")
        f.append("<title>Upload Status</title></head><body>")
        f.append("<h2>Upload Status</h2><hr>")
        if r:
            f.append("<strong>Success:</strong> " + info)
        else:
            f.append("<strong>Failed:</strong> " + info)
        f.append('<br><br><a href="{}">Back to directory</a>'.format(self.path))
        f.append("</body></html>")

        encoded = "\n".join(f).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def deal_post_data(self):
        """Parse POST payload and write file to current directory."""
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers["Content-Type"],
            },
        )

        if "file" not in form:
            return False, "No file field in upload request."

        fileitem = form["file"]
        if not fileitem.filename:
            return False, "No file selected."

        filename = os.path.basename(fileitem.filename)
        target_path = self.translate_path(self.path)

        if os.path.isdir(target_path):
            save_path = os.path.join(target_path, filename)
        else:
            save_path = target_path

        try:
            with open(save_path, "wb") as f:
                f.write(fileitem.file.read())
            return True, "File '{}' uploaded successfully.".format(filename)
        except Exception as e:
            return False, "Failed to write file: {}".format(str(e))


def run(port=8080, directory=None):
    if directory:
        os.chdir(directory)

    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("", port), DetailedHTTPRequestHandler)
    print("Serving HTTP and Camera Stream on port {}...".format(port))

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        if camera is not None:
            camera.stop_recording()
            camera.close()
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run an HTTP server with directory listing, uploads, and Pi camera streaming."
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8080,
        help="Port to serve on (default: 8080)",
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        default=None,
        help="Directory to serve (default: current directory)",
    )
    args = parser.parse_args()

    run(port=args.port, directory=args.directory)
