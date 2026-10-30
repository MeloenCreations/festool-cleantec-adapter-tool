#!/usr/bin/env python3
"""Render the adapter and check the socket, the tube, and the web tool."""

from __future__ import annotations

import os
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import generate  # noqa: E402


def render(scad: Path, stl: Path) -> str:
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    result = subprocess.run(
        ["openscad", "--export-format=binstl", "-o", str(stl), str(scad)],
        check=False,
        text=True,
        capture_output=True,
        env=env,
    )
    output = result.stdout + result.stderr
    if result.returncode != 0:
        raise AssertionError(f"OpenSCAD failed ({result.returncode}):\n{output}")
    return output


def echo_numbers(output: str) -> dict[str, float]:
    found = {}
    for name, value in re.findall(r"ECHO: (\w+) = ([-\d.]+)", output):
        found[name] = float(value)
    return found


def read_stl(path: Path):
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    import numpy as np

    verts = np.zeros((count, 3, 3), dtype=np.float64)
    for index in range(count):
        offset = 84 + index * 50
        verts[index] = np.frombuffer(data[offset + 12 : offset + 48], dtype="<f4").reshape(3, 3)
    return verts


def section_radii(verts, z: float, samples: int = 360):
    import numpy as np

    points = []
    for tri in verts:
        zz = tri[:, 2]
        if (zz >= z).all() or (zz < z).all():
            continue
        for i in range(3):
            a = tri[i]
            b = tri[(i + 1) % 3]
            if (a[2] - z) * (b[2] - z) < 0:
                t = (z - a[2]) / (b[2] - a[2])
                points.append(a + (b - a) * t)
    if not points:
        return np.array([]), np.array([])
    pts = np.array(points)
    radius = np.hypot(pts[:, 0], pts[:, 1])
    angle = np.degrees(np.arctan2(pts[:, 1], pts[:, 0])) % 360
    mins = np.full(samples, np.nan)
    maxs = np.full(samples, np.nan)
    for i in range(samples):
        selected = (angle >= i) & (angle < i + 1)
        if np.any(selected):
            mins[i] = radius[selected].min()
            maxs[i] = radius[selected].max()
    return mins, maxs


class GenerateTests(unittest.TestCase):
    def test_defaults_round_trip(self):
        source = generate.load_template()
        updated = generate.substitute(source, 28, "inner", 40, 3)
        self.assertIn('measurement = "inner";', updated)
        self.assertIn("diameter = 28;", updated)
        self.assertIn("wall_length = 40;", updated)
        self.assertIn("wall_thickness = 3;", updated)
        self.assertTrue(updated.startswith("// Tube inner diameter 28 mm"))

    def test_outer_measurement_is_rejected_when_the_wall_fills_the_tube(self):
        with self.assertRaises(ValueError):
            generate.substitute(generate.load_template(), 10, "outer", 40, 6)

    def test_page_embeds_the_current_scad_source(self):
        page = generate.build_page()
        self.assertNotIn(generate.PLACEHOLDER, page)
        self.assertIn("socket_od = 44.5;", page)
        self.assertIn("module locking_lip", page)
        committed = generate.INDEX_PATH.read_text(encoding="utf-8")
        self.assertEqual(committed, page)

    def test_page_transition_matches_the_model(self):
        page = generate.build_page()
        self.assertIn("Math.abs(tubeOd - SOCKET.od) * 0.7", page)
        self.assertIn("abs(tube_od - socket_od) * 0.7", page)


class RenderTests(unittest.TestCase):
    def render_case(self, diameter, measurement, length, thickness):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            scad = folder / "adapter.scad"
            stl = folder / "adapter.stl"
            text = generate.substitute(
                generate.load_template(), diameter, measurement, length, thickness
            )
            text = text.replace("resolution = 96;", "resolution = 48;", 1)
            scad.write_text(text, encoding="utf-8")
            output = render(scad, stl)
            return echo_numbers(output), read_stl(stl)

    def test_default_tube_and_socket(self):
        echoes, verts = self.render_case(28, "inner", 40, 3)
        self.assertAlmostEqual(echoes["Tube_ID"], 28)
        self.assertAlmostEqual(echoes["Tube_OD"], 34)
        self.assertAlmostEqual(echoes["Transition_h"], 8)
        self.assertAlmostEqual(echoes["Total_length"], 40 + 8 + 45.4)

        points = verts.reshape(-1, 3)
        self.assertAlmostEqual(points[:, 0].min(), -22.25, delta=0.05)
        self.assertAlmostEqual(points[:, 0].max(), 22.25, delta=0.05)
        self.assertAlmostEqual(points[:, 2].min(), -0.02, delta=0.03)
        self.assertAlmostEqual(points[:, 2].max(), echoes["Total_length"], delta=0.05)

        import numpy as np

        mins, maxs = section_radii(verts, 20)
        self.assertTrue(np.nanmax(maxs) < 17.2)
        self.assertTrue(np.nanmin(mins) > 13.8)

        def bins_of(mins, width=10):
            folded = []
            for start in range(0, 360, width):
                chunk = mins[start : start + width]
                if np.any(~np.isnan(chunk)):
                    folded.append(float(np.nanmin(chunk)))
            return np.array(folded)

        socket_base = 40 + 8
        lip_mins, lip_maxs = section_radii(verts, socket_base + 20.5)
        lip_bins = bins_of(lip_mins)
        bore = lip_bins[(lip_bins > 17.5) & (lip_bins < 19)]
        shelves = lip_bins[(lip_bins > 16.2) & (lip_bins < 17.4)]
        self.assertGreaterEqual(len(bore), 12)
        self.assertGreaterEqual(len(shelves), 8)
        self.assertAlmostEqual(float(np.median(bore)), 18.1, delta=0.15)
        # Two deeper shelves near 16.6 mm and one shallower shelf near 16.9 mm.
        deep = shelves[shelves < 16.75]
        shallow = shelves[shelves >= 16.75]
        self.assertGreaterEqual(len(deep), 4)
        self.assertGreaterEqual(len(shallow), 2)
        self.assertAlmostEqual(float(np.median(deep)), 16.6, delta=0.15)
        self.assertAlmostEqual(float(np.median(shallow)), 16.9, delta=0.15)
        self.assertAlmostEqual(float(np.nanmax(lip_maxs)), 22.25, delta=0.05)

        clear_bins = bins_of(section_radii(verts, socket_base + 30)[0])
        inner = clear_bins[clear_bins < 20]
        self.assertGreaterEqual(len(inner), 30)
        self.assertLess(int(np.sum(inner < 17.4)), 2)
        self.assertAlmostEqual(float(np.median(inner)), 18.1, delta=0.15)

    def test_outer_diameter_flares_past_the_socket(self):
        echoes, verts = self.render_case(60, "outer", 25, 3)
        self.assertAlmostEqual(echoes["Tube_ID"], 54)
        self.assertAlmostEqual(echoes["Tube_OD"], 60)
        points = verts.reshape(-1, 3)
        self.assertAlmostEqual(points[:, 0].max(), 30, delta=0.05)
        self.assertAlmostEqual(points[:, 2].max(), echoes["Total_length"], delta=0.05)

    def test_impossible_wall_does_not_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            scad = Path(tmp) / "bad.scad"
            source = generate.load_template()
            # Bypass the generator check so OpenSCAD's own assert is what fails.
            source = source.replace("diameter = 28;", "diameter = 10;", 1)
            source = source.replace('measurement = "inner";', 'measurement = "outer";', 1)
            source = source.replace("wall_thickness = 3;", "wall_thickness = 6;", 1)
            scad.write_text(source, encoding="utf-8")
            env = os.environ.copy()
            env["QT_QPA_PLATFORM"] = "offscreen"
            result = subprocess.run(
                ["openscad", "-o", str(Path(tmp) / "bad.stl"), str(scad)],
                check=False,
                text=True,
                capture_output=True,
                env=env,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("airflow", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
