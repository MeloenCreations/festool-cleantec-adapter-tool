#!/usr/bin/env python3
"""Write a Festool CLEANTEC adapter OpenSCAD file, or rebuild the web tool."""

from __future__ import annotations

import argparse
import math
import os
import re
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCAD_PATH = ROOT / "scad" / "cleantec_adapter.scad"
PAGE_TEMPLATE = ROOT / "web" / "page.template.html"
INDEX_PATH = ROOT / "index.html"
PLACEHOLDER = "___SCAD_SOURCE___"
SERVE_HOST = "127.0.0.1"
SERVE_PORT = 8765
RENDER_LOCK = threading.Lock()

PARAM_PATTERNS = {
    "diameter": re.compile(r"^diameter = [^;]+;", re.M),
    "measurement": re.compile(r'^measurement = "[^"]+";', re.M),
    "wall_length": re.compile(r"^wall_length = [^;]+;", re.M),
    "wall_thickness": re.compile(r"^wall_thickness = [^;]+;", re.M),
    "alignment": re.compile(r'^alignment = "[^"]+";', re.M),
    "angle": re.compile(r"^angle = [^;]+;", re.M),
}


def fmt(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("Values must be finite numbers.")
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return text if text not in ("", "-0") else "0"


def tube_diameters(diameter: float, measurement: str, thickness: float) -> tuple[float, float]:
    if measurement == "outer":
        return diameter - 2 * thickness, diameter
    if measurement == "inner":
        return diameter, diameter + 2 * thickness
    raise ValueError('measurement must be "inner" or "outer".')


def validate(
    diameter: float,
    measurement: str,
    length: float,
    thickness: float,
    alignment: str = "center",
    angle: float = 0,
) -> tuple[float, float]:
    if measurement not in ("inner", "outer"):
        raise ValueError('measurement must be "inner" or "outer".')
    if alignment not in ("center", "edge"):
        raise ValueError('alignment must be "center" or "edge".')
    for name, value in (("diameter", diameter), ("length", length), ("wall thickness", thickness)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name.capitalize()} must be a positive number.")
    if not math.isfinite(angle) or angle < -90 or angle > 90:
        raise ValueError("Angle must be from -90 to 90 degrees.")
    tube_id, tube_od = tube_diameters(diameter, measurement, thickness)
    if tube_id <= 0.5:
        raise ValueError(
            "Wall thickness leaves no airflow. Reduce it or increase the diameter."
        )
    return tube_id, tube_od


def substitute(
    source: str,
    diameter: float,
    measurement: str,
    length: float,
    thickness: float,
    alignment: str = "center",
    angle: float = 0,
) -> str:
    validate(diameter, measurement, length, thickness, alignment, angle)
    replacements = {
        "diameter": f"diameter = {fmt(diameter)};",
        "measurement": f'measurement = "{measurement}";',
        "wall_length": f"wall_length = {fmt(length)};",
        "wall_thickness": f"wall_thickness = {fmt(thickness)};",
        "alignment": f'alignment = "{alignment}";',
        "angle": f"angle = {fmt(angle)};",
    }
    updated = source
    for key, pattern in PARAM_PATTERNS.items():
        updated, count = pattern.subn(replacements[key], updated, count=1)
        if count != 1:
            raise RuntimeError(f"Could not find the {key} assignment in the OpenSCAD template.")
    note = (
        f"// Tube {measurement} diameter {fmt(diameter)} mm, "
        f"length {fmt(length)} mm, wall {fmt(thickness)} mm, "
        f"{alignment}, angle {fmt(angle)} deg.\n"
    )
    return note + updated


def load_template() -> str:
    return SCAD_PATH.read_text(encoding="utf-8")


def render_stl(scad_text: str, dest: Path) -> None:
    """Render an OpenSCAD model to a binary STL."""
    with RENDER_LOCK:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            scad_path = folder / "adapter.scad"
            stl_path = folder / "adapter.stl"
            scad_path.write_text(scad_text, encoding="utf-8")
            env = os.environ.copy()
            env["QT_QPA_PLATFORM"] = "offscreen"
            result = subprocess.run(
                ["openscad", "--export-format=binstl", "-o", str(stl_path), str(scad_path)],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            output = (result.stderr or "") + (result.stdout or "")
            if result.returncode != 0 or not stl_path.exists():
                detail = output.strip() or "OpenSCAD failed."
                raise RuntimeError(detail)
            dest.write_bytes(stl_path.read_bytes())


def make_server(port: int = SERVE_PORT) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def _cors(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(204)
            self._cors()
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            if self.path.split("?", 1)[0] not in ("/", "/index.html"):
                self.send_error(404)
                return
            data = INDEX_PATH.read_bytes()
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self) -> None:  # noqa: N802
            if self.path.split("?", 1)[0] != "/stl":
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0 or length > 1_000_000:
                self._send_text(400, "Unexpected model size.")
                return
            scad_text = self.rfile.read(length).decode("utf-8")
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    dest = Path(tmp) / "adapter.stl"
                    render_stl(scad_text, dest)
                    data = dest.read_bytes()
            except RuntimeError as exc:
                self._send_text(422, str(exc))
                return
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "model/stl")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_text(self, status: int, message: str) -> None:
            body = message.encode("utf-8", errors="replace")
            self.send_response(status)
            self._cors()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args) -> None:
            print(f"{self.address_string()} {fmt % args}")

    return ThreadingHTTPServer((SERVE_HOST, port), Handler)


def serve(port: int = SERVE_PORT) -> None:
    server = make_server(port)
    bound = server.server_address[1]
    print(f"Open http://{SERVE_HOST}:{bound}/")
    print("Download STL on that page renders the model with OpenSCAD.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.server_close()


def build_page(template: str | None = None) -> str:
    source = template if template is not None else load_template()
    if "</" in source:
        raise RuntimeError("The OpenSCAD source contains '</', which cannot be embedded in the page.")
    page = PAGE_TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in page:
        raise RuntimeError(f"{PAGE_TEMPLATE.name} is missing {PLACEHOLDER}.")
    return page.replace(PLACEHOLDER, source.rstrip() + "\n")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diameter", type=float, default=28, help="Tube diameter in mm (default 28).")
    parser.add_argument(
        "--measurement",
        choices=("inner", "outer"),
        default="inner",
        help="Whether --diameter is the inner or the outer diameter (default inner).",
    )
    parser.add_argument("--length", type=float, default=40, help="Straight tube length in mm (default 40).")
    parser.add_argument("--thickness", type=float, default=3, help="Tube wall thickness in mm (default 3).")
    parser.add_argument(
        "--alignment",
        choices=("center", "edge"),
        default="center",
        help="Center the tube, or shift it until one outer wall lines up with the socket (default center).",
    )
    parser.add_argument(
        "--angle",
        type=float,
        default=0,
        help="Bend between the socket and the tube, in degrees from -90 to 90 (default 0).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Where to write the file. A .stl suffix renders an STL; anything else writes OpenSCAD.",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help=f"Serve the page at http://{SERVE_HOST}:{SERVE_PORT}/ and render STL downloads with OpenSCAD.",
    )
    parser.add_argument(
        "--build-page",
        action="store_true",
        help="Rebuild index.html from the OpenSCAD source and the page template.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.build_page:
        INDEX_PATH.write_text(build_page(), encoding="utf-8")
        print(f"Wrote {INDEX_PATH.relative_to(ROOT)}")
    if args.output is None and not args.build_page and not args.serve:
        args.output = Path("-")
    if args.output is not None:
        text = substitute(
            load_template(),
            args.diameter,
            args.measurement,
            args.length,
            args.thickness,
            args.alignment,
            args.angle,
        )
        if str(args.output) == "-":
            sys.stdout.write(text)
        elif args.output.suffix.lower() == ".stl":
            args.output.parent.mkdir(parents=True, exist_ok=True)
            render_stl(text, args.output)
            print(f"Wrote {args.output}")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
            print(f"Wrote {args.output}")
    if args.serve:
        serve()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
