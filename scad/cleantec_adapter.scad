// Festool CLEANTEC adapter
//
// The top end is a female CLEANTEC socket. The male plug on a Festool
// D27 or D36 suction hose pushes in and twists to lock. The other end
// is a tube. Set the tube diameter, whether that diameter is the inside
// or the outside, the tube length, and the wall thickness. Optimize for
// 3D printing opens an inner diameter by 0.2 mm, or shrinks an outer
// diameter by 0.2 mm. The tube can stay centered or slide across until
// one outer wall lines up with the socket, and it can leave the socket
// at an angle from -90 to 90 degrees.
// Circles are divided into flats 0.25 mm wide, which is finer than a
// 0.4 mm nozzle line, so a Bambu H2D prints them round.
//
// The socket follows the real plug: a 36.2 mm bore and three locking
// shelves. Proportions were measured from Meister Edel's reference
// models (Printables 107234 and 98001) and the shelves were eased by
// about 0.2 mm so a typical FDM print can still turn and lock. If a
// printed socket is too tight or too loose, change lip_deep_r,
// lip_shallow_r, or bore_d by a tenth of a millimetre or two.
//
// Print with the tube end on the bed and the socket mouth facing up.
// The shelves are chamfered underneath, so they do not need supports.
// PETG is a sound default. Use three or four perimeters.

/* [Tube] */
// Diameter of the tube, in millimetres.
diameter = 28; // [1:0.1:200]

// Which face of the tube `diameter` measures.
measurement = "inner"; // [inner, outer]

// Ease the chosen diameter by 0.2 mm for a typical FDM print.
// An inner diameter is printed 0.2 mm larger. An outer diameter is printed 0.2 mm smaller.
optimize_print = false;

// Length of the straight tube, in millimetres.
// The socket and the transition are added on top of this.
wall_length = 40; // [1:0.5:500]

// Wall thickness of the tube and the transition, in millimetres.
wall_thickness = 3; // [0.4:0.1:20]

// Center the tube, or shift it so one outer wall lines up with the socket.
alignment = "center"; // [center, edge]

// Bend between the socket axis and the tube, in degrees.
// 0 is straight. Positive bends toward the flush edge, negative the other way.
angle = 0; // [-90:1:90]

/* [Print] */
// Longest flat on a circle, in millimetres.
// 0.25 mm is finer than a 0.4 mm nozzle line, so a Bambu H2D prints the
// cylinders round instead of as a polygon. Use 0.15 mm with a 0.2 mm nozzle.
facet = 0.25; // [0.1:0.05:1]

// Circle sides. 0 follows facet. A positive number forces that many sides.
resolution = 0; // [0:16:720]

/* [Hidden] */
// Female CLEANTEC socket, in millimetres.
socket_od = 44.5;
socket_h = 45.4;
// Air passage where the socket meets the transition.
socket_exit_d = 32;
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

allowance = optimize_print ? 0.2 : 0;
sized = (measurement == "outer") ? diameter - allowance : diameter + allowance;
tube_id = (measurement == "outer") ? sized - 2 * wall_thickness : sized;
tube_od = (measurement == "outer") ? sized : sized + 2 * wall_thickness;

assert(measurement == "inner" || measurement == "outer",
       "measurement must be \"inner\" or \"outer\"");
assert(diameter > 0 && wall_length > 0 && wall_thickness > 0,
       "Diameter, length, and wall thickness must be positive.");
assert(sized > 0,
       "The print allowance removes the whole diameter. Increase it or turn optimization off.");
assert(tube_id > 0.5,
       "Wall thickness leaves no airflow. Reduce it or increase the diameter.");
assert(alignment == "center" || alignment == "edge",
       "alignment must be \"center\" or \"edge\"");
assert(angle >= -90 && angle <= 90,
       "Angle must be from -90 to 90 degrees.");
assert(facet > 0, "Facet size must be positive.");

// Long enough that the outside cone stays within about 35 degrees of vertical.
transition_h = max(
    8,
    max(abs(tube_od - socket_od) * 0.7, abs(tube_id - socket_exit_d) * 0.7)
);

// Shift that puts the tube's +X wall on the socket's +X wall.
edge_offset = (alignment == "edge") ? (socket_od - tube_od) / 2 : 0;
// Centerline radius of a bend. Large enough that the passage stays open.
bend_r = max(socket_od, tube_od) * 0.8;
bend_steps = max(6, round(abs(angle) / 8));

bore_r = bore_d / 2;
eps = 0.02;

function smooth(t) = t * t * (3 - 2 * t);
function path_pos(t) =
    let (
        sweep = abs(angle) * t,
        side = angle < 0 ? -1 : 1
    ) [
        side * bend_r * (1 - cos(sweep)) + edge_offset * smooth(t),
        0,
        -bend_r * sin(sweep)
    ];
function path_dir(t) =
    let (
        a = max(0, t - 0.001),
        b = min(1, t + 0.001),
        d = path_pos(b) - path_pos(a)
    ) d;
function lerp(a, b, t) = a + (b - a) * t;

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

// Passage through the socket. The socket base is z = 0.
module socket_void() {
    translate([0, 0, -eps])
        cylinder(h = 6 + eps, r1 = socket_exit_d / 2, r2 = bore_r);
    translate([0, 0, 6 - eps])
        cylinder(h = 32.2 + 2 * eps, r = bore_r);
    translate([0, 0, 38.2 - eps])
        cylinder(h = 1.8 + 2 * eps, r1 = bore_r, r2 = mouth_d / 2);
    translate([0, 0, 40 - eps])
        cylinder(h = 3.8 + 2 * eps, r = mouth_d / 2);
    translate([0, 0, 43.8 - eps])
        cylinder(h = socket_h - 43.8 + 1,
                 r1 = mouth_d / 2, r2 = socket_od / 2 - 0.65);
}

module socket_lips() {
    locking_lip(lip_deep_r, lip_centers[0]);
    locking_lip(lip_deep_r, lip_centers[1]);
    locking_lip(lip_shallow_r, lip_centers[2]);
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
                cylinder(h = socket_h + eps, r = socket_od / 2);
        }

        union() {
            translate([0, 0, -1])
                cylinder(h = wall_length + 1 + eps, r = tube_id / 2);
            translate([0, 0, z_tube1 - eps])
                cylinder(h = transition_h + 2 * eps,
                         r1 = tube_id / 2, r2 = socket_exit_d / 2);
            translate([0, 0, z_sock0]) socket_void();
        }
    }

    translate([0, 0, z_sock0]) socket_lips();
}

// Straight tube, shifted so its +X wall is flush with the socket's +X wall.
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
                cylinder(h = socket_h + eps, r = socket_od / 2);
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
            translate([0, 0, z_sock0]) socket_void();
        }
    }

    translate([0, 0, z_sock0]) socket_lips();
}

module station(t, radius) {
    translate(path_pos(t))
        orient_z_to(path_dir(t))
            cylinder(h = 0.8, r = radius, center = true);
}

// Socket base at the origin. A positive angle bends toward +X, a negative angle toward -X.
module bent_adapter() {
    tube_dir = [sin(angle), 0, -cos(angle)];
    tube_end = path_pos(1) + tube_dir * wall_length;
    tz = tube_dir[2];
    rim = tube_od / 2 * sqrt(max(0, 1 - tz * tz));
    lowest = tube_end[2] - rim;

    translate([0, 0, -lowest]) {
        difference() {
            union() {
                for (i = [0 : bend_steps - 1]) {
                    hull() {
                        station(i / bend_steps, lerp(socket_od / 2, tube_od / 2, i / bend_steps));
                        station((i + 1) / bend_steps, lerp(socket_od / 2, tube_od / 2, (i + 1) / bend_steps));
                    }
                }
                translate(path_pos(1))
                    orient_z_to(tube_dir)
                        cylinder(h = wall_length, r = tube_od / 2);
                translate([0, 0, -eps])
                    cylinder(h = socket_h + eps, r = socket_od / 2);
            }

            union() {
                for (i = [0 : bend_steps - 1]) {
                    hull() {
                        station(i / bend_steps, lerp(socket_exit_d / 2, tube_id / 2, i / bend_steps));
                        station((i + 1) / bend_steps, lerp(socket_exit_d / 2, tube_id / 2, (i + 1) / bend_steps));
                    }
                }
                translate(path_pos(1) - tube_dir * 0.4)
                    orient_z_to(tube_dir)
                        cylinder(h = wall_length + 1.4, r = tube_id / 2);
                socket_void();
            }
        }

        socket_lips();
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

echo(Tube_ID = tube_id);
echo(Tube_OD = tube_od);
echo(Transition_h = transition_h);
echo(Total_length = wall_length + transition_h + socket_h);
echo(Edge_offset = edge_offset);
echo(Angle = angle);
echo(Bend_r = bend_r);
