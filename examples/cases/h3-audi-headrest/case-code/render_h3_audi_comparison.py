import argparse
import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def read_stl(path: Path, stride=1):
    with path.open("rb") as fh:
        fh.read(80)
        count = struct.unpack("<I", fh.read(4))[0]
        tris = []
        for i in range(count):
            raw = fh.read(50)
            if i % stride:
                continue
            vals = struct.unpack("<12fH", raw)
            tris.append(
                [
                    [vals[3], vals[4], vals[5]],
                    [vals[6], vals[7], vals[8]],
                    [vals[9], vals[10], vals[11]],
                ]
            )
    return np.asarray(tris, dtype=np.float64)


def rotation(ax, ay, az):
    ax, ay, az = [math.radians(v) for v in (ax, ay, az)]
    rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
    rz = np.array([[math.cos(az), -math.sin(az), 0], [math.sin(az), math.cos(az), 0], [0, 0, 1]])
    return rz @ ry @ rx


def render(tris, title, angles, bounds, width=480, height=360):
    img = Image.new("RGB", (width, height), (246, 248, 252))
    draw = ImageDraw.Draw(img)
    if len(tris) == 0:
        return img
    pts = tris.reshape(-1, 3)
    center = 0.5 * (bounds[0] + bounds[1])
    r = rotation(*angles)
    rpts = (pts - center) @ r.T
    bpts = (np.vstack([bounds[0], bounds[1]]) - center) @ r.T
    ext = np.abs(bpts).max(axis=0) * 2.0
    scale = min((width - 58) / max(ext[0], 1e-9), (height - 72) / max(ext[1], 1e-9))
    xy = rpts[:, :2] * scale
    xy[:, 0] += width / 2
    xy[:, 1] = height / 2 - xy[:, 1] + 12
    rtris = rpts.reshape(-1, 3, 3)
    xytris = xy.reshape(-1, 3, 2)
    order = np.argsort(rtris[:, :, 2].mean(axis=1))
    light = np.array([0.25, -0.45, 0.86], dtype=np.float64)
    light /= np.linalg.norm(light)
    for idx in order:
        tri = rtris[idx]
        n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
        ln = np.linalg.norm(n)
        shade = 0.58
        if ln > 1e-9:
            n /= ln
            shade = max(0.25, min(0.95, 0.58 + 0.34 * float(np.dot(n, light))))
        c = tuple(int(205 * shade + 35) for _ in range(3))
        draw.polygon([tuple(p) for p in xytris[idx]], fill=c)
    draw.rectangle((0, 0, width - 1, height - 1), outline=(202, 211, 224))
    draw.text((12, 10), title, fill=(22, 28, 36))
    return img


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, action="append")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--comparison", type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    sources = args.source or [root / "headrest_extraction" / "final_headrest_exports" / "quersus_h3_audi_cushion_shell_only.stl"]
    output = args.output or root / "headrest_h3_audi_smooth_pillow_delivery" / "h3_audi_smooth_pillow_single_solid_preview.stl"
    src = np.vstack([read_stl(source, stride=3) for source in sources])
    out = read_stl(output)

    # Normalize both models independently to compare shape, not absolute placement.
    src_pts = src.reshape(-1, 3)
    out_pts = out.reshape(-1, 3)
    src_center = 0.5 * (src_pts.min(axis=0) + src_pts.max(axis=0))
    out_center = 0.5 * (out_pts.min(axis=0) + out_pts.max(axis=0))
    src_size = np.ptp(src_pts, axis=0)
    out_size = np.ptp(out_pts, axis=0)
    out_norm = (out_pts - out_center) * (src_size / np.maximum(out_size, 1e-9)) + src_center
    out = out_norm.reshape(-1, 3, 3)

    bounds = np.vstack([src_pts.min(axis=0), src_pts.max(axis=0)])
    views = [
        ("ISO", (-22, 0, 35)),
        ("FRONT XZ", (0, 0, 0)),
        ("DEPTH SIDE", (0, 0, 90)),
        ("TOP XY", (90, 0, 0)),
    ]
    sheet = Image.new("RGB", (480 * 2, 360 * 4), (255, 255, 255))
    for row, (name, angles) in enumerate(views):
        sheet.paste(render(src, "SOURCE " + name, angles, bounds), (0, row * 360))
        sheet.paste(render(out, "OUTPUT " + name, angles, bounds), (480, row * 360))
    out_path = args.comparison or root / "headrest_h3_audi_smooth_pillow_delivery" / "source_vs_output_comparison.png"
    sheet.save(out_path)
    print(out_path)


if __name__ == "__main__":
    main()
