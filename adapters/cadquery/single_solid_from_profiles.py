import argparse
import json
from pathlib import Path

import cadquery as cq


def make_wire(profile):
    curve = profile["curve"]
    x = curve[0]["x"]
    y0, z0 = curve[0]["y"], curve[0]["z"]
    y1, z1 = curve[-1]["y"], curve[-1]["z"]

    bottom_left = cq.Vector(x, y0, 0.0)
    top_left = cq.Vector(x, y0, z0)
    top_right = cq.Vector(x, y1, z1)
    bottom_right = cq.Vector(x, y1, 0.0)
    top_points = [cq.Vector(x, p["y"], p["z"]) for p in curve]

    edges = [
        cq.Edge.makeLine(bottom_left, top_left),
        cq.Edge.makeSpline(top_points),
        cq.Edge.makeLine(top_right, bottom_right),
        cq.Edge.makeLine(bottom_right, bottom_left),
    ]
    return cq.Wire.assembleEdges(edges)


def main():
    parser = argparse.ArgumentParser(description="Build one closed BREP solid from ordered loft profile JSON.")
    parser.add_argument("profiles_json", type=Path)
    parser.add_argument("--step", type=Path, required=True)
    parser.add_argument("--preview-stl", type=Path)
    parser.add_argument("--ruled", action="store_true")
    args = parser.parse_args()

    data = json.loads(args.profiles_json.read_text(encoding="utf-8"))
    profiles = data["profiles"]
    wires = [make_wire(profile) for profile in profiles]
    solid = cq.Solid.makeLoft(wires, ruled=args.ruled)
    if solid is None:
        raise RuntimeError("makeLoft returned None")
    if not solid.isValid():
        raise RuntimeError("CadQuery/OCC loft solid is invalid")

    args.step.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(solid, str(args.step))
    if args.preview_stl:
        args.preview_stl.parent.mkdir(parents=True, exist_ok=True)
        cq.exporters.export(solid, str(args.preview_stl), tolerance=0.08, angularTolerance=0.08)

    print("VALID", solid.isValid())
    print("VOLUME_MM3", solid.Volume())
    print("FACES", len(solid.Faces()))
    print("SOLIDS", len(cq.Compound.makeCompound([solid]).Solids()))
    print("STEP", args.step)
    if args.preview_stl:
        print("STL", args.preview_stl)


if __name__ == "__main__":
    main()
