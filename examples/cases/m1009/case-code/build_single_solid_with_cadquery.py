import json
import os
from pathlib import Path

import cadquery as cq


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
DELIVERY = WORKSPACE / "native_loft_delivery"
FINAL = WORKSPACE / "最终交付_SLDPRT"
JSON_PATH = ROOT / "native_loft_profiles.json"

OUT_STEP = DELIVERY / "M1009_curved_face_block_single_solid.step"
OUT_STL = DELIVERY / "M1009_curved_face_block_single_solid_preview.stl"


def load_profiles():
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    profiles = data["profiles"]
    # Keep every fitted profile except the almost-duplicate mid section that made SolidWorks lofts unstable.
    if len(profiles) == 20:
        profiles = [profile for idx, profile in enumerate(profiles) if idx != 11]
    return profiles


def make_wire(profile):
    curve = profile["curve"]
    x = curve[0]["x"]
    y0, z0 = curve[0]["y"], curve[0]["z"]
    y1, z1 = curve[-1]["y"], curve[-1]["z"]

    p_bottom_left = cq.Vector(x, y0, 0.0)
    p_top_left = cq.Vector(x, y0, z0)
    p_top_right = cq.Vector(x, y1, z1)
    p_bottom_right = cq.Vector(x, y1, 0.0)

    top_points = [cq.Vector(x, p["y"], p["z"]) for p in curve]
    edges = [
        cq.Edge.makeLine(p_bottom_left, p_top_left),
        cq.Edge.makeSpline(top_points),
        cq.Edge.makeLine(p_top_right, p_bottom_right),
        cq.Edge.makeLine(p_bottom_right, p_bottom_left),
    ]
    return cq.Wire.assembleEdges(edges)


def build():
    DELIVERY.mkdir(exist_ok=True)
    FINAL.mkdir(exist_ok=True)
    profiles = load_profiles()
    wires = [make_wire(profile) for profile in profiles]
    solid = cq.Solid.makeLoft(wires, ruled=False)
    if solid is None:
        raise RuntimeError("makeLoft returned None")
    if not solid.isValid():
        raise RuntimeError("CadQuery loft solid is invalid")

    compound = cq.Compound.makeCompound([solid])
    print("VALID", solid.isValid())
    print("VOLUME_MM3", solid.Volume())
    print("FACES", len(solid.Faces()))
    print("SOLIDS", len(compound.Solids()))

    cq.exporters.export(solid, str(OUT_STEP))
    cq.exporters.export(solid, str(OUT_STL), tolerance=0.08, angularTolerance=0.08)
    print("STEP", OUT_STEP)
    print("STL", OUT_STL)


if __name__ == "__main__":
    build()
