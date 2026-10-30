#!/usr/bin/env python3
"""Write a Festool CLEANTEC adapter OpenSCAD file, or rebuild the web tool."""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCAD_PATH = ROOT / "scad" / "cleantec_adapter.scad"
PAGE_TEMPLATE = ROOT / "web" / "page.template.html"
INDEX_PATH = ROOT / "index.html"
PLACEHOLDER = "___SCAD_SOURCE___"

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
    if not math.isfinite(angle) or angle < 0 or angle > 90:
        raise ValueError("Angle must be from 0 to 90 degrees.")
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
        help="Bend between the socket and the tube, in degrees from 0 to 90 (default 0).",
    )
    parser.add_argument("-o", "--output", type=Path, help="Where to write the OpenSCAD file.")
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
    if args.output is None and not args.build_page:
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
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
            print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
