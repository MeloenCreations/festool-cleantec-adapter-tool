// Vacuum hose adapter
//
// The top end can be a female Festool CLEANTEC socket, a Dyson V6 tool
// connector, or a plain tube. The bottom end is a tube. Set each tube's
// diameter, whether that diameter is the inside or the outside, the tube
// length, and the wall thickness. Optimize for 3D printing opens an inner
// diameter by 0.2 mm, or shrinks an outer diameter by 0.2 mm, on every
// sized end (bottom tube, top tube, and the Dyson connector). The bottom
// tube can stay centered or slide across until one outer wall lines up
// with the top, and it can leave the top at an angle from -90 to 90
// degrees. An optional stopper ridge sits in the transition: inside,
// outside, or both. Set its length along the axis and its height out
// from the wall. On a bend the outer shoulder runs farther than the
// inner one. Optimize for 3D printing also tapers the stopper's top and
// bottom edges at 45 degrees so the overhang needs no support.
// Circles are divided into flats 0.25 mm wide, which is finer than a
// 0.4 mm nozzle line, so a Bambu H2D prints them round.
//
// The CLEANTEC socket follows the real plug: a 36.2 mm bore and three
// locking shelves. Proportions were measured from Meister Edel's
// reference models (Printables 107234 and 98001) and the shelves were
// eased by about 0.2 mm so a typical FDM print can still turn and lock.
// If a printed socket is too tight or too loose, change lip_deep_r,
// lip_shallow_r, or bore_d by a tenth of a millimetre or two.
//
// The Dyson V6 connector matches the male wand tip tools click onto
// (also DC35/DC45/DC52/DC58/DC59). A circumferential groove holds the
// tool latch, and four orientation flats sit near the base of the tip.
//
// Print with the bottom tube end on the bed and the top mouth facing up.
// CLEANTEC shelves are chamfered underneath, so they do not need supports.
// PETG is a sound default. Use three or four perimeters.

/* [Top] */
// What sits on the top end of the adapter.
top_style = "cleantec"; // [cleantec, dyson, tube]

// Diameter of the top tube, in millimetres. Used when top_style is tube.
top_diameter = 28; // [1:0.1:200]

// Which face of the top tube `top_diameter` measures.
top_measurement = "inner"; // [inner, outer]

// Length of the straight top tube, in millimetres. Used when top_style is tube.
top_wall_length = 40; // [1:0.5:500]

/* [Bottom tube] */
// Diameter of the bottom tube, in millimetres.
diameter = 28; // [1:0.1:200]

// Which face of the bottom tube `diameter` measures.
measurement = "inner"; // [inner, outer]

// Ease sized diameters by 0.2 mm for a typical FDM print.
// An inner diameter is printed 0.2 mm larger. An outer diameter is printed 0.2 mm smaller.
// Applies to the bottom tube, a top tube, and the Dyson connector.
optimize_print = false;

// Length of the straight bottom tube, in millimetres.
// The top end and the transition are added on top of this.
wall_length = 40; // [1:0.5:500]

// Wall thickness of the tubes and the transition, in millimetres.
wall_thickness = 3; // [0.4:0.1:20]

// Center the bottom tube, or shift it so one outer wall lines up with the top.
alignment = "center"; // [center, edge]

// Bend between the top axis and the bottom tube, in degrees.
// 0 is straight. Positive bends toward the flush edge, negative the other way.
angle = 0; // [-90:1:90]

/* [Stopper] */
// Ridge between the top and bottom. None disables it.
stopper_side = "none"; // [none, inside, outside, both]

// How far the stopper runs along the adapter axis, in millimetres.
stopper_length = 4; // [0.5:0.1:40]

// How far the stopper sticks out from the wall, in millimetres.
stopper_height = 3; // [0.5:0.1:40]

/* [Print] */
// Longest flat on a circle, in millimetres.
// 0.25 mm is finer than a 0.4 mm nozzle line, so a Bambu H2D prints the
// cylinders round instead of as a polygon. Use 0.15 mm with a 0.2 mm nozzle.
facet = 0.25; // [0.1:0.05:1]

// Circle sides. 0 follows facet. A positive number forces that many sides.
resolution = 0; // [0:16:720]

/* [Hidden] */
// Female CLEANTEC socket, in millimetres.
cleantec_od = 44.5;
cleantec_h = 45.4;
// Air passage where the socket meets the transition.
cleantec_exit_d = 32;
// Bore the plug body and its lugs slide through.
bore_d = 36.2;
// Lead-in counterbore at the mouth.
mouth_d = 40;
// Locking shelves. The plug's grooves bottom out near a radius of
// 16.5 mm; these sit just clear of that, and the lugs (radius 18 mm)
// still catch on the way out. The third shelf is shallower.
lip_deep_r = 16.6;
lip_shallow_r = 16.9;
lip_angle = 46;
// Height of the shelves above the socket base, and their thickness.
lip_z0 = 17;
lip_h = 7;
// Shelf centres in degrees. The last one is the shallow shelf.
lip_centers = [0, 120, 240];

// Dyson V6 male tool connector, in millimetres.
dyson_od_nom = 34.1;
dyson_id_nom = 28.5;
dyson_h = 46;
dyson_tip_h = 10;
dyson_groove_h = 4.45;
dyson_groove_taper_h = 2.75;
dyson_groove_d = 30.7;
dyson_clip_z = 37;
dyson_clip_len = 9.5;
dyson_clip_wall = 2.5;
dyson_clip_width = 3;

allowance = optimize_print ? 0.2 : 0;

function sized_diameter(d, face) =
    (face == "outer") ? d - allowance : d + allowance;

function diameters_from(d, face, thickness) =
    let (sized = sized_diameter(d, face))
        (face == "outer")
            ? [sized - 2 * thickness, sized]
            : [sized, sized + 2 * thickness];

bottom_pair = diameters_from(diameter, measurement, wall_thickness);
tube_id = bottom_pair[0];
tube_od = bottom_pair[1];
bottom_sized = sized_diameter(diameter, measurement);

top_pair = diameters_from(top_diameter, top_measurement, wall_thickness);
top_tube_id = top_pair[0];
top_tube_od = top_pair[1];
top_sized = sized_diameter(top_diameter, top_measurement);

dyson_od = dyson_od_nom - allowance;
dyson_id = dyson_id_nom;

socket_od =
    top_style == "cleantec" ? cleantec_od :
    top_style == "dyson" ? dyson_od :
    top_tube_od;
socket_exit_d =
    top_style == "cleantec" ? cleantec_exit_d :
    top_style == "dyson" ? dyson_id :
    top_tube_id;
socket_h =
    top_style == "cleantec" ? cleantec_h :
    top_style == "dyson" ? dyson_h :
    top_wall_length;

assert(top_style == "cleantec" || top_style == "dyson" || top_style == "tube",
       "top_style must be \"cleantec\", \"dyson\", or \"tube\"");
assert(measurement == "inner" || measurement == "outer",
       "measurement must be \"inner\" or \"outer\"");
assert(top_measurement == "inner" || top_measurement == "outer",
       "top_measurement must be \"inner\" or \"outer\"");
assert(diameter > 0 && wall_length > 0 && wall_thickness > 0,
       "Diameter, length, and wall thickness must be positive.");
assert(top_diameter > 0 && top_wall_length > 0,
       "Top diameter and top length must be positive.");
assert(bottom_sized > 0,
       "The print allowance removes the whole bottom diameter. Increase it or turn optimization off.");
assert(top_style != "tube" || top_sized > 0,
       "The print allowance removes the whole top diameter. Increase it or turn optimization off.");
assert(tube_id > 0.5,
       "Wall thickness leaves no airflow. Reduce it or increase the diameter.");
assert(top_style != "tube" || top_tube_id > 0.5,
       "Wall thickness leaves no airflow in the top tube. Reduce it or increase the top diameter.");
assert(alignment == "center" || alignment == "edge",
       "alignment must be \"center\" or \"edge\"");
assert(angle >= -90 && angle <= 90,
       "Angle must be from -90 to 90 degrees.");
assert(
    stopper_side == "none" || stopper_side == "inside" ||
    stopper_side == "outside" || stopper_side == "both",
    "stopper_side must be \"none\", \"inside\", \"outside\", or \"both\""
);
assert(stopper_side == "none" || (stopper_length > 0 && stopper_height > 0),
       "Stopper length and height must be positive.");
assert(facet > 0, "Facet size must be positive.");

stopper_on = stopper_side != "none";
stopper_inside = stopper_side == "inside" || stopper_side == "both";
stopper_outside = stopper_side == "outside" || stopper_side == "both";

// Long enough that the outside cone stays within about 35 degrees of vertical.
// A stopper sits in this band, so keep room for its length.
transition_h = max(
    8,
    max(
        max(abs(tube_od - socket_od) * 0.7, abs(tube_id - socket_exit_d) * 0.7),
        stopper_on ? stopper_length : 0
    )
);

min_bore_r = min(tube_id, socket_exit_d) / 2;
assert(
    !stopper_inside || min_bore_r - stopper_height > 0.5,
    "Inside stopper closes the airflow. Reduce stopper height or increase the diameter."
);
// 45° print tapers on the stopper's top and bottom edges when optimizing.
stopper_chamfer = (optimize_print && stopper_on)
    ? min(stopper_height, stopper_length / 2)
    : 0;

// Shift that puts the tube's +X wall on the top's +X wall.
edge_offset = (alignment == "edge") ? (socket_od - tube_od) / 2 : 0;
// Centerline radius of a bend. Large enough that the passage stays open.
bend_r = max(socket_od, tube_od) * 0.8;
bend_steps = max(6, round(abs(angle) / 8));

bore_r = bore_d / 2;
eps = 0.02;

// Along one edge the centerline eases onto the flush wall while it turns.
// The run is long enough that this bend stays gentler than the tube radius.
// A short shift kinks both walls, especially at a small angle.
blend_len = (alignment == "edge")
    ? max(
        transition_h,
        max(
            sqrt(8 * abs(edge_offset) * tube_od),
            bend_r * abs(angle) * 0.01745329252
        )
    )
    : 0;
blend_steps = max(16, round(blend_len / 2));

function smooth(t) = t * t * (3 - 2 * t);
function lerp(a, b, t) = a + (b - a) * t;
function blend_delta(i) =
    let (
        s0 = (i - 1) / blend_steps,
        s1 = i / blend_steps,
        heading = angle * smooth((s0 + s1) / 2)
    ) [
        blend_len * sin(heading) / blend_steps + edge_offset * (smooth(s1) - smooth(s0)),
        0,
        -blend_len * cos(heading) / blend_steps
    ];
function blend_pos(i) = i <= 0 ? [0, 0, 0] : blend_pos(i - 1) + blend_delta(i);
function blend_outer_r(i) = lerp(socket_od / 2, tube_od / 2, smooth(i / blend_steps));
function blend_inner_r(i) = lerp(socket_exit_d / 2, tube_id / 2, smooth(i / blend_steps));
function arc_pos(u) =
    let (
        sweep = abs(angle) * u,
        side = angle < 0 ? -1 : 1
    ) [
        side * bend_r * (1 - cos(sweep)),
        0,
        -bend_r * sin(sweep)
    ];
function arc_dir(u) =
    let (
        sweep = abs(angle) * u,
        side = angle < 0 ? -1 : 1
    ) [side * sin(sweep), 0, -cos(sweep)];
function arc_outer_r(u) = lerp(socket_od / 2, tube_od / 2, u);
function arc_inner_r(u) = lerp(socket_exit_d / 2, tube_id / 2, u);

// Radial extra of the stopper ridge at distance s along its length.
// With optimize_print this rises and falls at 45 degrees so the overhang
// needs no support when the bottom tube sits on the bed.
function stopper_extra(s) =
    let (
        rise = stopper_chamfer > 0
            ? min(s, stopper_length - s, stopper_chamfer) *
              (stopper_height / stopper_chamfer)
            : stopper_height
    ) max(0, min(stopper_height, rise));

module locking_lip(r_in, center_deg) {
    $fn = resolution;
    translate([0, 0, lip_z0])
        rotate([0, 0, center_deg - lip_angle / 2])
            rotate_extrude(angle = lip_angle, convexity = 4)
                polygon([
                    [bore_r + 0.2, 0],
                    [bore_r + 0.2, lip_h],
                    [r_in + 0.8, lip_h],
                    [r_in, lip_h - 0.8],
                    [r_in, 1.6]
                ]);
}

// Turn +Z to the requested direction and draw the children there.
module orient_z_to(dir) {
    length = norm(dir);
    d = dir / length;
    ax = [-d[1], d[0], 0];
    ang = atan2(sqrt(d[0] * d[0] + d[1] * d[1]), d[2]);
    if (norm(ax) < 1e-8) {
        if (d[2] < 0)
            rotate([180, 0, 0]) children();
        else
            children();
    } else {
        rotate(a = ang, v = ax) children();
    }
}

// Passage through the CLEANTEC socket. The socket base is z = 0.
module cleantec_void() {
    translate([0, 0, -eps])
        cylinder(h = 6 + eps, r1 = cleantec_exit_d / 2, r2 = bore_r);
    translate([0, 0, 6 - eps])
        cylinder(h = 32.2 + 2 * eps, r = bore_r);
    translate([0, 0, 38.2 - eps])
        cylinder(h = 1.8 + 2 * eps, r1 = bore_r, r2 = mouth_d / 2);
    translate([0, 0, 40 - eps])
        cylinder(h = 3.8 + 2 * eps, r = mouth_d / 2);
    translate([0, 0, 43.8 - eps])
        cylinder(h = cleantec_h - 43.8 + 1,
                 r1 = mouth_d / 2, r2 = cleantec_od / 2 - 0.65);
}

module cleantec_lips() {
    locking_lip(lip_deep_r, lip_centers[0]);
    locking_lip(lip_deep_r, lip_centers[1]);
    locking_lip(lip_shallow_r, lip_centers[2]);
}

// Male Dyson V6 tool tip. Tools slide on from +Z. Base is z = 0.
// Built as one solid of revolution plus four shallow collar notches so the
// mesh stays a single manifold volume.
module dyson_solid() {
    od_r = dyson_od / 2;
    groove_r = dyson_groove_d / 2;
    clip_r = od_r + dyson_clip_wall;
    tip_z1 = dyson_tip_h;
    tip_z2 = tip_z1 + dyson_groove_h;
    tip_z3 = tip_z2 + dyson_groove_taper_h;
    clip_z0 = dyson_clip_z - 0.5;
    clip_z1 = clip_z0 + dyson_clip_len;

    // Profile on the +X side, spun around Z. The retaining groove is a
    // reduced outer radius; the collar is a short thicker band.
    rotate_extrude(convexity = 6)
        polygon([
            [0, 0],
            [od_r, 0],
            [od_r, tip_z1],
            [groove_r, tip_z1],
            [groove_r, tip_z2],
            [od_r, tip_z3],
            [od_r, clip_z0],
            [clip_r, clip_z0],
            [clip_r, clip_z1],
            [od_r, clip_z1],
            [0, clip_z1],
        ]);
}

module dyson_void() {
    od_r = dyson_od / 2;
    id_r = dyson_id / 2;
    clip_z0 = dyson_clip_z - 0.5;

    // Air passage.
    translate([0, 0, -eps])
        cylinder(h = dyson_h + 2 * eps, r = id_r);

    // Four orientation notches in the collar. Each cut stops short of the
    // main shaft so the collar stays one piece.
    translate([0, 0, clip_z0 - eps])
        for (a = [0, 90, 180, 270])
            rotate([0, 0, a])
                translate([
                    -(dyson_clip_width + 1) / 2,
                    -(od_r + dyson_clip_wall + 0.2),
                    0
                ])
                    cube([
                        dyson_clip_width + 1,
                        dyson_clip_wall + 0.4,
                        dyson_clip_len + 2 * eps
                    ]);
}

module top_void() {
    if (top_style == "cleantec")
        cleantec_void();
    else if (top_style == "dyson")
        dyson_void();
    else
        translate([0, 0, -eps])
            cylinder(h = top_wall_length + 2 * eps, r = top_tube_id / 2);
}

module top_solid() {
    if (top_style == "cleantec")
        cylinder(h = cleantec_h + eps, r = cleantec_od / 2);
    else if (top_style == "dyson")
        dyson_solid();
    else
        cylinder(h = top_wall_length + eps, r = top_tube_od / 2);
}

module top_extras() {
    if (top_style == "cleantec")
        cleantec_lips();
}

// Hull of solid disks, then cut the bore so the ridge stays annular.
// Hulling rings directly would fill the passage.
module stopper_pair(pos0, dir0, outer0, inner0, extra0,
                    pos1, dir1, outer1, inner1, extra1) {
    thick = 0.8;
    if (stopper_outside && (extra0 > 0 || extra1 > 0))
        difference() {
            hull() {
                translate(pos0) orient_z_to(dir0)
                    cylinder(h = thick, r = outer0 + extra0, center = true);
                translate(pos1) orient_z_to(dir1)
                    cylinder(h = thick, r = outer1 + extra1, center = true);
            }
            hull() {
                translate(pos0) orient_z_to(dir0)
                    cylinder(h = thick + 2 * eps, r = max(eps, outer0 - 0.05), center = true);
                translate(pos1) orient_z_to(dir1)
                    cylinder(h = thick + 2 * eps, r = max(eps, outer1 - 0.05), center = true);
            }
        }
    if (stopper_inside && (extra0 > 0 || extra1 > 0))
        difference() {
            hull() {
                translate(pos0) orient_z_to(dir0)
                    cylinder(h = thick, r = inner0 + 0.05, center = true);
                translate(pos1) orient_z_to(dir1)
                    cylinder(h = thick, r = inner1 + 0.05, center = true);
            }
            hull() {
                translate(pos0) orient_z_to(dir0)
                    cylinder(h = thick + 2 * eps, r = max(eps, inner0 - extra0), center = true);
                translate(pos1) orient_z_to(dir1)
                    cylinder(h = thick + 2 * eps, r = max(eps, inner1 - extra1), center = true);
            }
        }
}

// Straight stopper between the tube and the top, centred on the transition.
module straight_stopper(z_tube1, z_sock0, tube_shift = 0) {
    if (stopper_on) {
        z0 = z_sock0 - transition_h / 2 - stopper_length / 2;
        steps = max(4, round(stopper_length / 1.2));
        for (i = [0 : steps - 1]) {
            s0 = i * stopper_length / steps;
            s1 = (i + 1) * stopper_length / steps;
            t0 = (z0 + s0 - z_tube1) / transition_h;
            t1 = (z0 + s1 - z_tube1) / transition_h;
            // Blend the tube's edge shift out across the transition.
            off0 = tube_shift * (1 - smooth(max(0, min(1, t0))));
            off1 = tube_shift * (1 - smooth(max(0, min(1, t1))));
            outer0 = lerp(tube_od / 2, socket_od / 2, max(0, min(1, t0)));
            outer1 = lerp(tube_od / 2, socket_od / 2, max(0, min(1, t1)));
            inner0 = lerp(tube_id / 2, socket_exit_d / 2, max(0, min(1, t0)));
            inner1 = lerp(tube_id / 2, socket_exit_d / 2, max(0, min(1, t1)));
            stopper_pair(
                [off0, 0, z0 + s0], [0, 0, 1], outer0, inner0, stopper_extra(s0),
                [off1, 0, z0 + s1], [0, 0, 1], outer1, inner1, stopper_extra(s1)
            );
        }
    }
}

// Stopper that follows the bent transition. The shoulder on the outside of
// the elbow runs farther than the inside, so that wall stretches.
module bent_stopper(edge) {
    if (stopper_on) {
        path_len = edge ? blend_len : bend_r * abs(angle) * 0.01745329252;
        span = min(stopper_length, max(path_len, 0.1));
        // Centre the band on the middle of the transition path.
        s_mid = path_len / 2;
        s_start = max(0, s_mid - span / 2);
        steps = max(4, round(span / 1.2));
        for (i = [0 : steps - 1]) {
            a0 = s_start + i * span / steps;
            a1 = s_start + (i + 1) * span / steps;
            u0 = path_len > 0 ? a0 / path_len : 0;
            u1 = path_len > 0 ? a1 / path_len : 0;
            // Distance along the stopper band itself (for the 45° taper).
            d0 = a0 - s_start;
            d1 = a1 - s_start;
            if (edge) {
                i0 = max(0, min(blend_steps, round(u0 * blend_steps)));
                i1 = max(0, min(blend_steps, round(u1 * blend_steps)));
                dir0 = blend_delta(max(1, min(blend_steps, i0 + 1)));
                dir1 = blend_delta(max(1, min(blend_steps, i1 + 1)));
                stopper_pair(
                    blend_pos(i0), dir0, blend_outer_r(i0), blend_inner_r(i0), stopper_extra(d0),
                    blend_pos(i1), dir1, blend_outer_r(i1), blend_inner_r(i1), stopper_extra(d1)
                );
            } else {
                stopper_pair(
                    arc_pos(u0), arc_dir(u0), arc_outer_r(u0), arc_inner_r(u0), stopper_extra(d0),
                    arc_pos(u1), arc_dir(u1), arc_outer_r(u1), arc_inner_r(u1), stopper_extra(d1)
                );
            }
        }
    }
}

module centered_adapter() {
    z_tube1 = wall_length;
    z_sock0 = wall_length + transition_h;

    difference() {
        union() {
            translate([0, 0, -eps])
                cylinder(h = wall_length + 2 * eps, r = tube_od / 2);
            translate([0, 0, z_tube1 - eps])
                cylinder(h = transition_h + 2 * eps,
                         r1 = tube_od / 2, r2 = socket_od / 2);
            translate([0, 0, z_sock0 - eps])
                top_solid();
        }

        union() {
            translate([0, 0, -1])
                cylinder(h = wall_length + 1 + eps, r = tube_id / 2);
            translate([0, 0, z_tube1 - eps])
                cylinder(h = transition_h + 2 * eps,
                         r1 = tube_id / 2, r2 = socket_exit_d / 2);
            translate([0, 0, z_sock0]) top_void();
        }
    }

    translate([0, 0, z_sock0]) top_extras();
    straight_stopper(z_tube1, z_sock0);
}

// Straight tube, shifted so its +X wall is flush with the top's +X wall.
module edge_adapter() {
    z_tube1 = wall_length;
    z_sock0 = wall_length + transition_h;

    difference() {
        union() {
            translate([edge_offset, 0, -eps])
                cylinder(h = wall_length + 2 * eps, r = tube_od / 2);
            hull() {
                translate([edge_offset, 0, z_tube1])
                    cylinder(h = 0.4, r = tube_od / 2, center = true);
                translate([0, 0, z_sock0])
                    cylinder(h = 0.4, r = socket_od / 2, center = true);
            }
            translate([0, 0, z_sock0 - eps])
                top_solid();
        }

        union() {
            translate([edge_offset, 0, -1])
                cylinder(h = wall_length + 1 + eps, r = tube_id / 2);
            hull() {
                translate([edge_offset, 0, z_tube1])
                    cylinder(h = 0.4, r = tube_id / 2, center = true);
                translate([0, 0, z_sock0 + 0.2])
                    cylinder(h = 0.4, r = socket_exit_d / 2, center = true);
            }
            translate([0, 0, z_sock0]) top_void();
        }
    }

    translate([0, 0, z_sock0]) top_extras();
    straight_stopper(z_tube1, z_sock0, edge_offset);
}

module arc_station(u, radius) {
    translate(arc_pos(u))
        orient_z_to(arc_dir(u))
            cylinder(h = 0.8, r = radius, center = true);
}

module disk_at(pos, dir, radius) {
    translate(pos)
        orient_z_to(dir)
            cylinder(h = 0.8, r = radius, center = true);
}

// Top base at the origin. A positive angle bends toward +X, a negative angle toward -X.
// Along one edge, one smooth curve shifts the tube onto the flush wall as it turns.
module bent_adapter() {
    edge = alignment == "edge";
    tube_dir = edge
        ? blend_delta(blend_steps) / norm(blend_delta(blend_steps))
        : arc_dir(1);
    tube_origin = edge ? blend_pos(blend_steps) : arc_pos(1);
    tube_end = tube_origin + tube_dir * wall_length;
    tz = tube_dir[2];
    rim = tube_od / 2 * sqrt(max(0, 1 - tz * tz));
    lowest = tube_end[2] - rim;

    translate([0, 0, -lowest]) {
        difference() {
            union() {
                if (edge) {
                    for (i = [0 : blend_steps - 1]) {
                        hull() {
                            disk_at(blend_pos(i), blend_delta(i + 1), blend_outer_r(i));
                            disk_at(blend_pos(i + 1), blend_delta(min(blend_steps, i + 2)), blend_outer_r(i + 1));
                        }
                    }
                } else {
                    for (i = [0 : bend_steps - 1]) {
                        hull() {
                            arc_station(i / bend_steps, arc_outer_r(i / bend_steps));
                            arc_station((i + 1) / bend_steps, arc_outer_r((i + 1) / bend_steps));
                        }
                    }
                }
                translate(tube_origin)
                    orient_z_to(tube_dir)
                        cylinder(h = wall_length, r = tube_od / 2);
                translate([0, 0, -eps])
                    top_solid();
            }

            union() {
                if (edge) {
                    for (i = [0 : blend_steps - 1]) {
                        hull() {
                            disk_at(blend_pos(i), blend_delta(i + 1), blend_inner_r(i));
                            disk_at(blend_pos(i + 1), blend_delta(min(blend_steps, i + 2)), blend_inner_r(i + 1));
                        }
                    }
                } else {
                    for (i = [0 : bend_steps - 1]) {
                        hull() {
                            arc_station(i / bend_steps, arc_inner_r(i / bend_steps));
                            arc_station((i + 1) / bend_steps, arc_inner_r((i + 1) / bend_steps));
                        }
                    }
                }
                translate(tube_origin - tube_dir * 0.4)
                    orient_z_to(tube_dir)
                        cylinder(h = wall_length + 1.4, r = tube_id / 2);
                top_void();
            }
        }

        top_extras();
        bent_stopper(edge);
    }
}

module adapter_body() {
    if (angle == 0 && alignment != "edge")
        centered_adapter();
    else if (angle == 0)
        edge_adapter();
    else
        bent_adapter();
}

module forced_resolution() {
    $fn = resolution;
    children();
}

// Flats no longer than `facet`, and no coarser than 0.5 degrees.
module smooth_resolution() {
    $fn = 0;
    $fa = 0.5;
    $fs = facet;
    children();
}

module adapter() {
    if (resolution > 0)
        forced_resolution() adapter_body();
    else
        smooth_resolution() adapter_body();
}

adapter();

echo(Top_style = top_style);
echo(Tube_ID = tube_id);
echo(Tube_OD = tube_od);
echo(Top_ID = socket_exit_d);
echo(Top_OD = socket_od);
echo(Transition_h = transition_h);
echo(Total_length = wall_length + transition_h + socket_h);
echo(Edge_offset = edge_offset);
echo(Angle = angle);
echo(Bend_r = bend_r);
echo(Blend_len = blend_len);
echo(Stopper_side = stopper_side);
echo(Stopper_length = stopper_on ? stopper_length : 0);
echo(Stopper_height = stopper_on ? stopper_height : 0);
echo(Stopper_chamfer = stopper_chamfer);
