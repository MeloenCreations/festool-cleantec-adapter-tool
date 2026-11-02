# Vacuum hose adapter

A small tool that writes an OpenSCAD model of a vacuum adapter. The top end can be a female Festool CLEANTEC socket, a Dyson V6 tool connector, or a plain tube. The bottom end is a tube you size.

| Setting | Default | Meaning |
| --- | --- | --- |
| Top connector | CLEANTEC | CLEANTEC socket, Dyson V6 male tip, or a sized tube |
| Top diameter / face | 28 mm inner | Used when the top is a tube |
| Top tube length | 40 mm | Used when the top is a tube |
| Bottom diameter | 28 mm | Size of the bottom tube |
| Inner or outer | Inner | Which face that bottom diameter measures |
| Optimize for 3D printing | Off | Ease sized diameters, the Dyson outer, and the CLEANTEC bore/shelves by the print allowance; also cuts stopper outer corners at 45° |
| Print allowance | 0.2 mm | Clearance used when optimize is on: inner diameters grow, outer diameters shrink |
| Bottom tube length | 40 mm | Length of the straight bottom tube |
| Wall thickness | 3 mm | Thickness of the tube walls |
| Position | Centered | Centered, or slid until one outer wall lines up with the top |
| Angle | 0° | Bend from −90° to 90°. Positive bends toward the flush edge |
| Stopper | None | Ridge in the transition: inside, outside, or both |
| Stopper length | 4 mm | How far the ridge runs along the adapter |
| Stopper height | 3 mm | How far the ridge sticks out from the wall |

CLEANTEC and Dyson keep their own shape. A short cone joins the top to the bottom tube. With the defaults the bottom tube is 28 mm inside and 34 mm outside. On a bend the stopper’s outer shoulder runs farther than the inner one. Optimize for 3D printing also cuts the stopper’s outer corners at 45° to its horizontal top and bottom edges so the overhang needs no support.

## Use the page

Open `index.html` in a browser. The section drawing updates as you change the numbers. **Download SCAD file** saves the OpenSCAD source.

**Download STL file** renders that same model. Start the local helper, then open the address it prints:

```bash
python3 generate.py --serve
```

A straight STL usually finishes within a minute. A bend takes longer. The cylinders are divided into flats 0.25 mm wide, which is finer than a 0.4 mm nozzle line, so a Bambu H2D prints them round.

## Use OpenSCAD directly

`scad/cleantec_adapter.scad` is the same model. The Customizer panel edits the top style, tube settings, edge alignment, and bend angle. The CLEANTEC socket fit (bore and locking shelves) and the Dyson tip dimensions are in the hidden section of the file if a print needs a tenth of a millimetre more clearance.

## Use the command line

```bash
python3 generate.py --diameter 28 --measurement inner --length 40 --thickness 3 --alignment edge --angle -45 -o adapter.scad
python3 generate.py --top dyson --diameter 32 --measurement outer --optimize-print -o adapter.scad
python3 generate.py --top tube --top-diameter 40 --top-measurement outer --diameter 28 --measurement inner -o adapter.scad
python3 generate.py --stopper both --stopper-length 5 --stopper-height 3 --optimize-print --print-allowance 0.3 -o adapter.scad
python3 generate.py --diameter 28 --measurement inner --length 40 --thickness 3 -o adapter.stl
```

`--top` is `cleantec`, `dyson`, or `tube`. `--measurement` / `--top-measurement` are `inner` or `outer`. `--stopper` is `none`, `inside`, `outside`, or `both`. `--optimize-print` eases sized diameters by `--print-allowance` (default 0.2 mm): an inner 28 mm becomes 28.2 mm, an outer 28 mm becomes 27.8 mm, a Dyson tip shrinks by the same amount on the outside, and a CLEANTEC bore, mouth, exit, and locking shelves open by the same amount; it also cuts stopper outer corners at 45° to the horizontal edges. `--alignment` is `center` or `edge`. `--angle` is degrees from -90 to 90. A `.stl` output renders the model with OpenSCAD. The command checks that the wall thickness still leaves a passage and that the angle is in range.

After changing `scad/cleantec_adapter.scad` or `web/page.template.html`, rebuild the page:

```bash
python3 generate.py --build-page
```

## Printing

Place the bottom tube on the bed and the top mouth facing up. CLEANTEC locking shelves are chamfered on the underside, so a straight adapter does not need supports. A bend may need support inside the elbow. PETG is a good default. Three or four perimeters keep the wall airtight.

The CLEANTEC socket is a tight fit. Turn on Optimize for 3D printing so the bore and shelves open by the print allowance. If the hose plug still will not turn, open the generated file and raise `lip_deep_r_nom` and `lip_shallow_r_nom` by 0.1 mm or 0.2 mm, or increase the allowance.

## Top ends

**CLEANTEC.** The female socket is a 44.5 mm body with a 36.2 mm bore, a 40 mm lead-in at the mouth, and three locking shelves. Two shelves reach a radius of 16.6 mm and the third reaches 16.9 mm, which matches the slightly uneven CLEANTEC plug. The proportions were measured from Meister Edel's reference models on Printables (107234 and 98001) and eased by about 0.2 mm so a typical FDM print can still twist and lock. Optimize for 3D printing opens those inner faces further by the print allowance; the outer shell stays 44.5 mm.

**Dyson V6.** A male tip like a stock accessory: 34.1 mm across with a 28.5 mm smooth bore and an outer retaining groove for the vacuum latch. It plugs into a V6 / DC35/DC45/DC52/DC58/DC59. Nothing inside the tip is needed for locking. Optimize for 3D printing shrinks the outer diameter by the print allowance.

**Tube.** Same inner/outer diameter controls as the bottom end. Optimize for 3D printing eases that diameter by the print allowance the same way.
