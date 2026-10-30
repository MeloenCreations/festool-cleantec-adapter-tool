# Festool CLEANTEC adapter

A small tool that writes an OpenSCAD model of a vacuum adapter. One end is a female Festool CLEANTEC socket. The male plug on a D27 or D36 suction hose pushes in and twists to lock. The other end is a tube.

The tube is set with six values:

| Setting | Default | Meaning |
| --- | --- | --- |
| Diameter | 28 mm | Size of the tube |
| Inner or outer | Inner | Which face that diameter measures |
| Tube length | 40 mm | Length of the straight tube |
| Wall thickness | 3 mm | Thickness of the tube wall |
| Position | Centered | Centered, or slid until one outer wall lines up with the socket |
| Angle | 0° | Bend away from the socket axis, from 0° (straight) to 90° (a right angle) |

The socket keeps the CLEANTEC shape. A short cone joins it to the tube. With the defaults the tube is 28 mm inside and 34 mm outside.

## Use the page

Open `index.html` in a browser. The section drawing updates as you change the numbers. **Download SCAD file** saves a model with those values filled in.

Open that file in [OpenSCAD](https://openscad.org/), press F6 to render, and export an STL.

## Use OpenSCAD directly

`scad/cleantec_adapter.scad` is the same model. The Customizer panel edits the tube settings, including the edge alignment and the bend angle. The socket fit (bore and locking shelves) is in the hidden section of the file if a print needs a tenth of a millimetre more clearance.

## Use the command line

```bash
python3 generate.py --diameter 28 --measurement inner --length 40 --thickness 3 --alignment edge --angle 45 -o adapter.scad
```

`--measurement` is `inner` or `outer`. `--alignment` is `center` or `edge`. `--angle` is degrees from 0 to 90. The command checks that the wall thickness still leaves a passage and that the angle is in range, then writes the OpenSCAD file.

After changing `scad/cleantec_adapter.scad` or `web/page.template.html`, rebuild the page:

```bash
python3 generate.py --build-page
```

## Printing

Place the tube on the bed and the socket mouth facing up. The locking shelves are chamfered on the underside, so a straight adapter does not need supports. A bend may need support inside the elbow. PETG is a good default. Three or four perimeters keep the wall airtight.

The socket is a tight fit. If the hose plug will not turn, open the generated file and raise `lip_deep_r` and `lip_shallow_r` by 0.1 mm or 0.2 mm.

## Socket

The female socket is a 44.5 mm body with a 36.2 mm bore, a 40 mm lead-in at the mouth, and three locking shelves. Two shelves reach a radius of 16.6 mm and the third reaches 16.9 mm, which matches the slightly uneven CLEANTEC plug. The proportions were measured from Meister Edel's reference models on Printables (107234 and 98001) and eased by about 0.2 mm so a typical FDM print can still twist and lock.
