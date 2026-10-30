// Festool CLEANTEC adapter
//
// The top end is a female CLEANTEC socket. The male plug on a Festool
// D27 or D36 suction hose pushes in and twists to lock. The other end
// is a straight tube. Set the tube diameter, whether that diameter is
// the inside or the outside, the tube length, and the wall thickness.
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

// Length of the straight tube, in millimetres.
// The socket and the transition are added on top of this.
wall_length = 40; // [1:0.5:500]

// Wall thickness of the tube and the transition, in millimetres.
wall_thickness = 3; // [0.4:0.1:20]

/* [Print] */
// Circle smoothness. 96 is a good balance of roundness and render time.
resolution = 96; // [48:16:192]

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

tube_id = (measurement == "outer") ? diameter - 2 * wall_thickness : diameter;
tube_od = (measurement == "outer") ? diameter : diameter + 2 * wall_thickness;

assert(measurement == "inner" || measurement == "outer",
       "measurement must be \"inner\" or \"outer\"");
assert(diameter > 0 && wall_length > 0 && wall_thickness > 0,
       "Diameter, length, and wall thickness must be positive.");
assert(tube_id > 0.5,
       "Wall thickness leaves no airflow. Reduce it or increase the diameter.");

// Long enough that the outside cone stays within about 35 degrees of vertical.
transition_h = max(
    8,
    max(abs(tube_od - socket_od) * 0.7, abs(tube_id - socket_exit_d) * 0.7)
);

bore_r = bore_d / 2;
eps = 0.02;

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

module adapter() {
    $fn = resolution;
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
            // Passage inside the socket, heights relative to the socket base.
            translate([0, 0, z_sock0 - eps])
                cylinder(h = 6 + eps, r1 = socket_exit_d / 2, r2 = bore_r);
            translate([0, 0, z_sock0 + 6 - eps])
                cylinder(h = 32.2 + 2 * eps, r = bore_r);
            translate([0, 0, z_sock0 + 38.2 - eps])
                cylinder(h = 1.8 + 2 * eps, r1 = bore_r, r2 = mouth_d / 2);
            translate([0, 0, z_sock0 + 40 - eps])
                cylinder(h = 3.8 + 2 * eps, r = mouth_d / 2);
            translate([0, 0, z_sock0 + 43.8 - eps])
                cylinder(h = socket_h - 43.8 + 1,
                         r1 = mouth_d / 2, r2 = socket_od / 2 - 0.65);
        }
    }

    translate([0, 0, z_sock0]) {
        locking_lip(lip_deep_r, lip_centers[0]);
        locking_lip(lip_deep_r, lip_centers[1]);
        locking_lip(lip_shallow_r, lip_centers[2]);
    }
}

adapter();

echo(Tube_ID = tube_id);
echo(Tube_OD = tube_od);
echo(Transition_h = transition_h);
echo(Total_length = wall_length + transition_h + socket_h);
