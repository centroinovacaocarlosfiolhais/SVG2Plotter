#!/usr/bin/env python3
"""
SVG2Plotter — Inkscape Extension
─────────────────────────────────────────────────────────────────────
Sends the current Inkscape document to a running SVG2Plotter Network
server (http://<host>:<port>/api/...) for cutting on the SK1350.

No extra Python dependencies — uses only stdlib (urllib, json, sys).

Centro de Inovação Carlos Fiolhais · CDI Portugal
© 2026 David Marques — Vibe Coding with Claude.ai
CC BY-NC-ND 4.0
"""

import sys
import os
import json
import tempfile
import urllib.request
import urllib.error

# ── Inkscape extension API ────────────────────────────────────────────────────
# Try to import inkex (present when running inside Inkscape).
# Falls back to a minimal shim so the script can be tested standalone.
try:
    import inkex
    from inkex import Effect
    HAS_INKEX = True
except ImportError:
    HAS_INKEX = False

# ── Helpers ───────────────────────────────────────────────────────────────────

def api(host, port, path, method="GET", data=None, files=None, timeout=10):
    """
    Minimal HTTP client — no requests, no dependencies, pure stdlib.
    Supports GET, POST with JSON body, and multipart file upload.
    Returns (ok: bool, body: dict | str).
    """
    url = f"http://{host}:{port}/api{path}"

    try:
        if files:
            # ── Multipart form upload ─────────────────────────────────────
            boundary = "----SVG2PlotterBoundary7733"
            body_parts = []

            for field_name, (filename, filedata, content_type) in files.items():
                body_parts.append(
                    f"--{boundary}\r\n"
                    f"Content-Disposition: form-data; name=\"{field_name}\"; "
                    f"filename=\"{filename}\"\r\n"
                    f"Content-Type: {content_type}\r\n\r\n"
                )

            encoded = b""
            for part in body_parts:
                encoded += part.encode("utf-8")
                encoded += filedata
                encoded += b"\r\n"
            encoded += f"--{boundary}--\r\n".encode("utf-8")

            req = urllib.request.Request(url, data=encoded, method="POST")
            req.add_header("Content-Type",
                           f"multipart/form-data; boundary={boundary}")
            req.add_header("Content-Length", str(len(encoded)))

        elif data is not None:
            encoded = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(url, data=encoded, method=method)
            req.add_header("Content-Type", "application/json")

        else:
            req = urllib.request.Request(url, method=method)

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            try:
                return True, json.loads(body)
            except json.JSONDecodeError:
                return True, body

    except urllib.error.URLError as e:
        return False, str(e.reason)
    except Exception as e:
        return False, str(e)


def get_svg_bytes(svg_file):
    """Read SVG bytes from a file path."""
    with open(svg_file, "rb") as f:
        return f.read()


def run(svg_file, host, port, scale, mirror, test_only):
    """
    Main logic:
      1. Check server is reachable
      2. If test_only → run connection test and return
      3. Upload the SVG to the server
      4. Apply scale if != 1.0
      5. Trigger cut job
      6. Return result message
    """
    messages = []

    def log(msg):
        messages.append(msg)

    base_url = f"http://{host}:{port}"
    log(f"SVG2Plotter Network — {base_url}")
    log(f"Scale: {scale:.2f}×  |  Mode: {'MIRROR' if mirror else 'NORMAL'}")

    # ── 1. Reachability check ─────────────────────────────────────────────────
    ok, resp = api(host, port, "/ports")
    if not ok:
        return False, [
            f"Cannot reach SVG2Plotter Network at {base_url}",
            f"Error: {resp}",
            "",
            "Make sure the server is running:",
            "  python network/server.py",
            f"  Expected: http://{host}:{port}",
        ]
    log(f"Server reachable. Ports: {resp.get('ports', [])}")

    # ── 2. Test only ──────────────────────────────────────────────────────────
    if test_only:
        ok, resp = api(host, port, "/test", method="POST")
        if ok and resp.get("ok"):
            return True, [f"Connection test OK — {resp.get('msg', '')}"]
        else:
            return False, [
                "Connection test FAILED",
                str(resp.get("error", resp)),
                "",
                "Check that the cutter is connected and the port is selected in the server.",
            ]

    # ── 3. Upload SVG ─────────────────────────────────────────────────────────
    svg_bytes  = get_svg_bytes(svg_file)
    svg_name   = os.path.basename(svg_file)
    if not svg_name.endswith(".svg"):
        svg_name = "inkscape_export.svg"

    log(f"Uploading {svg_name} ({len(svg_bytes)} bytes)...")
    ok, resp = api(host, port, "/upload", files={
        "files": (svg_name, svg_bytes, "image/svg+xml")
    })

    if not ok or not resp.get("ok"):
        return False, [
            "Upload failed",
            str(resp.get("error", resp) if isinstance(resp, dict) else resp),
        ]

    uploaded = resp.get("uploaded", [])
    if not uploaded or uploaded[0].get("error"):
        return False, [
            "Server rejected the SVG",
            str(uploaded[0].get("error", "unknown") if uploaded else "no files received"),
        ]

    svg_id = uploaded[0].get("id")
    w_mm   = uploaded[0].get("w_mm", 0)
    h_mm   = uploaded[0].get("h_mm", 0)
    log(f"Uploaded OK — id:{svg_id}  {w_mm:.1f}×{h_mm:.1f}mm")

    # ── 4. Apply scale ────────────────────────────────────────────────────────
    if abs(scale - 1.0) > 0.001:
        ok, resp = api(host, port, "/scale", method="POST",
                       data={"id": svg_id, "scale": scale})
        if ok:
            log(f"Scale {scale:.2f}× applied")
        else:
            log(f"Warning: could not apply scale — {resp}")

    # ── 5. Apply mirror setting ───────────────────────────────────────────────
    ok, _ = api(host, port, "/settings", method="POST",
                data={"mirror": mirror})

    # ── 6. Send job ───────────────────────────────────────────────────────────
    log("Sending cut job...")
    ok, resp = api(host, port, "/send", method="POST")

    if not ok or not resp.get("ok"):
        return False, messages + [
            "Failed to start cut job",
            str(resp.get("error", resp) if isinstance(resp, dict) else resp),
            "",
            "Open the browser interface for details:",
            f"  {base_url}",
        ]

    log("Job started.")
    log("")
    log(f"Monitor progress at: {base_url}")
    return True, messages


# ── Inkscape extension entry point ────────────────────────────────────────────

class SVG2PlotterEffect(Effect if HAS_INKEX else object):

    def __init__(self):
        if HAS_INKEX:
            super().__init__()
            self.arg_parser.add_argument("--host",      type=str,   default="localhost")
            self.arg_parser.add_argument("--port",      type=int,   default=7733)
            self.arg_parser.add_argument("--scale",     type=float, default=1.0)
            self.arg_parser.add_argument("--mirror",    type=inkex.Boolean, default=False)
            self.arg_parser.add_argument("--test_only", type=inkex.Boolean, default=False)

    def effect(self):
        host      = self.options.host.strip()
        port      = self.options.port
        scale     = self.options.scale
        mirror    = self.options.mirror
        test_only = self.options.test_only

        # Inkscape passes the SVG as a temp file
        svg_file = self.options.input_file

        success, messages = run(svg_file, host, port, scale, mirror, test_only)

        msg = "\n".join(messages)

        if success:
            inkex.utils.debug(msg)
        else:
            inkex.errormsg(msg)


# ── Standalone / CLI mode ─────────────────────────────────────────────────────
# Useful for testing outside Inkscape:
#   python svg2plotter_send.py myfile.svg --host 192.168.1.100 --test
#   python svg2plotter_send.py myfile.svg

def cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="SVG2Plotter Inkscape Extension — CLI mode")
    parser.add_argument("svg_file",            help="Path to SVG file")
    parser.add_argument("--host",  default="localhost",
                        help="SVG2Plotter Network host (default: localhost)")
    parser.add_argument("--port",  type=int, default=7733,
                        help="Server port (default: 7733)")
    parser.add_argument("--scale", type=float, default=1.0,
                        help="Scale factor (default: 1.0)")
    parser.add_argument("--mirror",    action="store_true",
                        help="Mirror mode (glass/window)")
    parser.add_argument("--test-only", action="store_true",
                        help="Test connection only, do not cut")

    args = parser.parse_args()

    if not os.path.exists(args.svg_file):
        print(f"Error: file not found: {args.svg_file}")
        sys.exit(1)

    success, messages = run(
        args.svg_file, args.host, args.port,
        args.scale, args.mirror, args.test_only
    )

    for m in messages:
        print(m)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    if HAS_INKEX:
        SVG2PlotterEffect().run()
    else:
        cli()
