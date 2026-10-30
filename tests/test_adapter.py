#!/usr/bin/env python3
"""Render the adapter and check the socket, the tube, and the web tool."""

from __future__ import annotations

import os
import re
import struct
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request
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
    if "Simple:        yes" not in output:
        raise AssertionError(f"OpenSCAD mesh is not manifold:\n{output}")
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


def _radii_about(verts, z: float, center_x: float):
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
        return np.array([])
    pts = np.array(points)
    return np.hypot(pts[:, 0] - center_x, pts[:, 1])


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

    def test_alignment_and_angle_are_written(self):
        updated = generate.substitute(
            generate.load_template(), 32, "outer", 50, 2.5, "edge", 45
        )
        self.assertIn('alignment = "edge";', updated)
        self.assertIn("angle = 45;", updated)
        self.assertTrue(
            updated.startswith(
                "// Tube outer diameter 32 mm, length 50 mm, wall 2.5 mm, edge, angle 45 deg.\n"
            )
        )

    def test_angle_and_alignment_are_rejected_when_invalid(self):
        source = generate.load_template()
        with self.assertRaises(ValueError):
            generate.substitute(source, 28, "inner", 40, 3, "center", 91)
        with self.assertRaises(ValueError):
            generate.substitute(source, 28, "inner", 40, 3, angle=-91)
        with self.assertRaises(ValueError):
            generate.substitute(source, 28, "inner", 40, 3, "sideways")
        updated = generate.substitute(source, 28, "inner", 40, 3, angle=-90)
        self.assertIn("angle = -90;", updated)
        generate.substitute(source, 28, "inner", 40, 3, angle=90)

    def test_page_offers_edge_and_angle(self):
        page = generate.build_page()
        self.assertIn('name="alignment" value="edge"', page)
        self.assertIn('id="angle"', page)
        self.assertIn('min="-90"', page)
        self.assertIn('id="download-stl"', page)
        self.assertIn("Angle must be from -90 to 90 degrees.", page)
        self.assertIn("facet = 0.25;", page)
        self.assertIn('", angle " + fmt(spec.angle) + " deg" +', page)
        self.assertIn('id="optimize"', page)
        self.assertIn(
            "An inner diameter is printed 0.2 mm larger, an outer diameter 0.2 mm smaller.",
            page,
        )

    def test_print_fit_eases_the_chosen_diameter(self):
        source = generate.load_template()
        inner = generate.substitute(source, 28, "inner", 40, 3, optimize=True)
        self.assertIn("diameter = 28;", inner)
        self.assertIn("optimize_print = true;", inner)
        self.assertTrue(
            inner.startswith(
                "// Tube inner diameter 28 mm, length 40 mm, wall 3 mm, "
                "center, angle 0 deg, print fit 0.2 mm.\n"
            )
        )
        outer = generate.substitute(source, 28, "outer", 40, 3, optimize=True)
        self.assertIn("optimize_print = true;", outer)
        self.assertTrue(
            outer.startswith(
                "// Tube outer diameter 28 mm, length 40 mm, wall 3 mm, "
                "center, angle 0 deg, print fit 0.2 mm.\n"
            )
        )
        plain = generate.substitute(source, 28, "inner", 40, 3)
        self.assertIn("optimize_print = false;", plain)
        self.assertNotIn("print fit", plain)
        with self.assertRaises(ValueError):
            generate.substitute(source, 0.2, "outer", 40, 0.4, optimize=True)


class RenderTests(unittest.TestCase):
    def render_case(
        self, diameter, measurement, length, thickness, alignment="center", angle=0, optimize=False
    ):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            scad = folder / "adapter.scad"
            stl = folder / "adapter.stl"
            text = generate.substitute(
                generate.load_template(),
                diameter,
                measurement,
                length,
                thickness,
                alignment,
                angle,
                optimize,
            )
            text = text.replace("resolution = 0;", "resolution = 48;", 1)
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

    def test_print_fit_opens_an_inner_diameter(self):
        echoes, verts = self.render_case(28, "inner", 40, 3, optimize=True)
        self.assertAlmostEqual(echoes["Tube_ID"], 28.2)
        self.assertAlmostEqual(echoes["Tube_OD"], 34.2)
        import numpy as np

        mins, maxs = section_radii(verts, 20)
        self.assertAlmostEqual(float(np.nanmin(mins)), 14.1, delta=0.15)
        self.assertAlmostEqual(float(np.nanmax(maxs)), 17.1, delta=0.15)

    def test_print_fit_shrinks_an_outer_diameter(self):
        echoes, verts = self.render_case(28, "outer", 40, 3, optimize=True)
        self.assertAlmostEqual(echoes["Tube_ID"], 21.8)
        self.assertAlmostEqual(echoes["Tube_OD"], 27.8)
        import numpy as np

        mins, maxs = section_radii(verts, 20)
        self.assertAlmostEqual(float(np.nanmin(mins)), 10.9, delta=0.15)
        self.assertAlmostEqual(float(np.nanmax(maxs)), 13.9, delta=0.15)

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

    def test_edge_alignment_puts_the_tube_on_one_wall(self):
        echoes, verts = self.render_case(28, "inner", 40, 3, alignment="edge")
        self.assertAlmostEqual(echoes["Edge_offset"], 5.25)
        import numpy as np

        points = []
        z = 20
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
        pts = np.array(points)
        self.assertAlmostEqual(float(pts[:, 0].min()), -11.75, delta=0.05)
        self.assertAlmostEqual(float(pts[:, 0].max()), 22.25, delta=0.05)
        self.assertAlmostEqual(float(pts[:, 0].min() + pts[:, 0].max()) / 2, 5.25, delta=0.05)

    def test_right_angle_keeps_the_socket_and_turns_the_tube(self):
        echoes, verts = self.render_case(28, "inner", 40, 3, angle=90)
        points = verts.reshape(-1, 3)
        bend_r = echoes["Bend_r"]
        tube_r = echoes["Tube_OD"] / 2
        self.assertAlmostEqual(float(points[:, 0].max()), bend_r + 40, delta=0.05)
        self.assertAlmostEqual(float(points[:, 2].max()), bend_r + tube_r + 45.4, delta=0.05)
        self.assertAlmostEqual(float(points[:, 2].min()), 0, delta=0.05)
        self.assertAlmostEqual(float(points[:, 0].min()), -22.25, delta=0.05)

        import numpy as np

        shelf_z = bend_r + tube_r + 20.5
        mins, maxs = section_radii(verts, shelf_z)
        folded = []
        for start in range(0, 360, 10):
            chunk = mins[start : start + 10]
            if np.any(~np.isnan(chunk)):
                folded.append(float(np.nanmin(chunk)))
        folded = np.array(folded)
        shelves = folded[(folded > 16.2) & (folded < 17.4)]
        self.assertGreaterEqual(len(shelves), 8)
        self.assertAlmostEqual(float(np.nanmax(maxs)), 22.25, delta=0.05)

    def test_edge_and_right_angle_render_together(self):
        echoes, verts = self.render_case(28, "inner", 40, 3, alignment="edge", angle=90)
        points = verts.reshape(-1, 3)
        self.assertAlmostEqual(echoes["Lead_h"], 8)
        self.assertAlmostEqual(
            float(points[:, 0].max()),
            echoes["Bend_r"] + echoes["Edge_offset"] + 40,
            delta=0.1,
        )
        self.assertAlmostEqual(
            float(points[:, 2].max()),
            echoes["Lead_h"] + echoes["Bend_r"] + echoes["Tube_OD"] / 2 + 45.4,
            delta=0.1,
        )

    def test_edge_and_small_angle_do_not_pinch_the_wall(self):
        echoes, verts = self.render_case(28, "inner", 40, 3, alignment="edge", angle=6)
        import math

        import numpy as np

        lead = echoes["Lead_h"]
        bend_r = echoes["Bend_r"]
        offset = echoes["Edge_offset"]
        tube_r = echoes["Tube_OD"] / 2
        self.assertAlmostEqual(lead, 8)
        self.assertAlmostEqual(offset, 5.25)
        angle = 6 * math.pi / 180
        tube_end_z = -lead - bend_r * math.sin(angle) - math.cos(angle) * 40
        rim = tube_r * math.sqrt(max(0, 1 - math.cos(angle) ** 2))
        lift = -(tube_end_z - rim)

        # Midway along the straight taper the flush wall is still the socket's wall,
        # and the passage stays open by about the wall thickness.
        center_x = offset * 0.5
        outer_r = 22.25 + (tube_r - 22.25) * 0.5
        inner_r = 16 + (echoes["Tube_ID"] / 2 - 16) * 0.5
        radii = _radii_about(verts, lift - lead * 0.5, center_x)
        self.assertGreater(len(radii), 20)
        self.assertAlmostEqual(float(radii.max()), outer_r, delta=0.35)
        self.assertAlmostEqual(float(radii.min()), inner_r, delta=0.35)
        self.assertGreater(float(radii.max() - radii.min()), 2.5)

        points = verts.reshape(-1, 3)
        self.assertAlmostEqual(float(points[:, 2].min()), 0, delta=0.08)

    def test_angle_limit_is_enforced_by_the_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            scad = Path(tmp) / "bad.scad"
            source = generate.load_template().replace("angle = 0;", "angle = 91;", 1)
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
        self.assertIn("90", result.stderr + result.stdout)

    def test_negative_angle_bends_the_other_way(self):
        echoes, verts = self.render_case(28, "inner", 40, 3, angle=-90)
        points = verts.reshape(-1, 3)
        bend_r = echoes["Bend_r"]
        self.assertAlmostEqual(float(points[:, 0].min()), -(bend_r + 40), delta=0.05)
        self.assertAlmostEqual(float(points[:, 0].max()), 22.25, delta=0.05)
        self.assertAlmostEqual(
            float(points[:, 2].max()), bend_r + echoes["Tube_OD"] / 2 + 45.4, delta=0.05
        )
        self.assertAlmostEqual(float(points[:, 2].min()), 0, delta=0.05)

    def test_default_circles_are_fine_enough_to_print_round(self):
        text = generate.substitute(generate.load_template(), 28, "inner", 40, 3)
        self.assertIn("$fs = facet;", text)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            scad = folder / "adapter.scad"
            stl = folder / "adapter.stl"
            scad.write_text(text, encoding="utf-8")
            render(scad, stl)
            verts = read_stl(stl)
        import numpy as np

        z = 20
        radii = []
        for tri in verts:
            zz = tri[:, 2]
            if (zz >= z).all() or (zz < z).all():
                continue
            for i in range(3):
                a = tri[i]
                b = tri[(i + 1) % 3]
                if (a[2] - z) * (b[2] - z) < 0:
                    t = (z - a[2]) / (b[2] - a[2])
                    point = a + (b - a) * t
                    radius = float(np.hypot(point[0], point[1]))
                    if radius > 16.9:
                        radii.append((float(np.degrees(np.arctan2(point[1], point[0])) % 360), radius))
        angles = np.array(sorted(angle for angle, radius in radii if radius > 16.98))
        steps = np.diff(angles)
        steps = steps[steps > 0.05]
        chord = 2 * 17 * np.sin(np.median(steps) * np.pi / 360)
        # Flats of about 1 mm (the old 96-side circles) show on a Bambu H2D.
        self.assertLess(float(chord), 0.35)
        self.assertGreater(len(steps), 200)

    def test_server_returns_an_stl(self):
        text = generate.substitute(generate.load_template(), 28, "inner", 40, 3)
        text = text.replace("resolution = 0;", "resolution = 24;", 1)
        server = generate.make_server(0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            request = urllib.request.Request(
                f"http://127.0.0.1:{server.server_address[1]}/stl",
                data=text.encode("utf-8"),
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read()
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers["Access-Control-Allow-Origin"], "*")
        finally:
            server.shutdown()
            server.server_close()
        count = struct.unpack_from("<I", data, 80)[0]
        self.assertGreater(count, 100)
        self.assertEqual(len(data), 84 + count * 50)


if __name__ == "__main__":
    unittest.main()
