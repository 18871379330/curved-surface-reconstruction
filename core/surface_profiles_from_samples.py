import argparse
import csv
import json
import struct
from collections import defaultdict
from pathlib import Path

import numpy as np


def read_binary_stl(path: Path):
    with path.open("rb") as fh:
        fh.read(80)
        count = struct.unpack("<I", fh.read(4))[0]
        raw = fh.read(count * 50)
    tris = np.empty((count, 3, 3), dtype=np.float64)
    for i in range(count):
        vals = struct.unpack_from("<12fH", raw, i * 50)
        tris[i, 0] = vals[3:6]
        tris[i, 1] = vals[6:9]
        tris[i, 2] = vals[9:12]
    return tris.reshape(-1, 3), tris


def read_obj(path: Path):
    verts = []
    tris = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("v "):
            parts = line.split()
            verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
        elif line.startswith("f "):
            idx = []
            for token in line.split()[1:]:
                idx.append(int(token.split("/")[0]) - 1)
            for i in range(1, len(idx) - 1):
                tris.append([verts[idx[0]], verts[idx[i]], verts[idx[i + 1]]])
    pts = np.asarray(verts, dtype=np.float64)
    tri_arr = np.asarray(tris, dtype=np.float64) if tris else None
    return pts, tri_arr


def read_ascii_ply(path: Path):
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if not lines or not lines[0].strip() == "ply":
        raise ValueError("Only ASCII PLY is supported by this lightweight reader.")
    vertex_count = 0
    face_count = 0
    header_end = None
    for i, line in enumerate(lines):
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "element" and parts[1] == "vertex":
            vertex_count = int(parts[2])
        if len(parts) >= 3 and parts[0] == "element" and parts[1] == "face":
            face_count = int(parts[2])
        if line.strip() == "end_header":
            header_end = i + 1
            break
    if header_end is None:
        raise ValueError("PLY header has no end_header.")
    verts = []
    for line in lines[header_end:header_end + vertex_count]:
        parts = line.split()
        verts.append([float(parts[0]), float(parts[1]), float(parts[2])])
    faces_start = header_end + vertex_count
    tris = []
    for line in lines[faces_start:faces_start + face_count]:
        parts = [int(x) for x in line.split()]
        n = parts[0]
        idx = parts[1:1 + n]
        for i in range(1, len(idx) - 1):
            tris.append([verts[idx[0]], verts[idx[i]], verts[idx[i + 1]]])
    pts = np.asarray(verts, dtype=np.float64)
    tri_arr = np.asarray(tris, dtype=np.float64) if tris else None
    return pts, tri_arr


def read_points(path: Path):
    rows = []
    delimiter = "," if path.suffix.lower() == ".csv" else None
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as fh:
        reader = csv.reader(fh, delimiter=delimiter) if delimiter else (line.split() for line in fh)
        for parts in reader:
            if len(parts) < 3:
                continue
            try:
                rows.append([float(parts[0]), float(parts[1]), float(parts[2])])
            except ValueError:
                continue
    return np.asarray(rows, dtype=np.float64), None


def load_geometry(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".stl":
        return read_binary_stl(path)
    if suffix == ".obj":
        return read_obj(path)
    if suffix == ".ply":
        return read_ascii_ply(path)
    if suffix in {".xyz", ".pts", ".csv"}:
        return read_points(path)
    raise ValueError(f"Unsupported input format: {suffix}")


def mesh_stats(pts: np.ndarray, tris):
    stats = {
        "points": int(len(pts)),
        "triangles": int(len(tris)) if tris is not None else 0,
        "open_edges": None,
        "nonmanifold_edges": None,
        "degenerate_faces": None,
        "signed_volume": None,
        "positive_volume": None,
    }
    if tris is None or len(tris) == 0:
        return stats

    key_to_idx = {}
    edge_counts = defaultdict(int)
    degenerate = 0
    signed_volume = 0.0
    for tri in tris:
        face = []
        for p in tri:
            key = tuple(np.round(p / 1e-6).astype(np.int64))
            idx = key_to_idx.get(key)
            if idx is None:
                idx = len(key_to_idx)
                key_to_idx[key] = idx
            face.append(idx)
        if len(set(face)) != 3:
            degenerate += 1
            continue
        for edge in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            edge_counts[tuple(sorted(edge))] += 1
        signed_volume += float(np.dot(tri[0], np.cross(tri[1], tri[2])) / 6.0)

    stats.update({
        "vertices": int(len(key_to_idx)),
        "open_edges": int(sum(v == 1 for v in edge_counts.values())),
        "nonmanifold_edges": int(sum(v > 2 for v in edge_counts.values())),
        "degenerate_faces": int(degenerate),
        "signed_volume": signed_volume,
        "positive_volume": bool(abs(signed_volume) > 1e-9),
    })
    return stats


def poly_terms(x, y, degree):
    cols = []
    for total in range(degree + 1):
        for px in range(total + 1):
            py = total - px
            cols.append((x ** px) * (y ** py))
    return np.vstack(cols).T


def fit_surface(samples, mn, mx, degree):
    x = (samples[:, 0] - mn[0]) / max(mx[0] - mn[0], 1e-9) * 2.0 - 1.0
    y = (samples[:, 1] - mn[1]) / max(mx[1] - mn[1], 1e-9) * 2.0 - 1.0
    z = samples[:, 2]
    keep = np.ones(len(samples), dtype=bool)
    coef = None
    for _ in range(6):
        coef = np.linalg.lstsq(poly_terms(x[keep], y[keep], degree), z[keep], rcond=None)[0]
        pred = poly_terms(x, y, degree) @ coef
        resid = z - pred
        med = float(np.median(resid[keep]))
        mad = float(np.median(np.abs(resid[keep] - med)) + 1e-9)
        limit = max(5.0, 3.0 * 1.4826 * mad)
        new_keep = np.abs(resid - med) < limit
        if new_keep.sum() < max(30, len(samples) // 3) or np.array_equal(new_keep, keep):
            break
        keep = new_keep
    return coef, int(keep.sum())


def eval_surface(coef, x, y, mn, mx, degree):
    xs = (np.asarray(x) - mn[0]) / max(mx[0] - mn[0], 1e-9) * 2.0 - 1.0
    ys = (np.asarray(y) - mn[1]) / max(mx[1] - mn[1], 1e-9) * 2.0 - 1.0
    return poly_terms(xs, ys, degree) @ coef


def high_surface_samples(pts, mn, mx, base_z, grid_x, grid_y):
    xi = np.clip(((pts[:, 0] - mn[0]) / (mx[0] - mn[0]) * (grid_x - 1)).astype(int), 0, grid_x - 1)
    yi = np.clip(((pts[:, 1] - mn[1]) / (mx[1] - mn[1]) * (grid_y - 1)).astype(int), 0, grid_y - 1)
    top = {}
    for xb, yb, x, y, z in zip(xi, yi, pts[:, 0], pts[:, 1], pts[:, 2]):
        if z <= base_z + 2.0:
            continue
        key = (int(xb), int(yb))
        cur = top.get(key)
        if cur is None or z > cur[2]:
            top[key] = (float(x), float(y), float(z))
    return np.asarray(list(top.values()), dtype=np.float64)


def main():
    parser = argparse.ArgumentParser(description="Sample a mesh/point-cloud target face and emit ordered loft profile JSON.")
    parser.add_argument("input", type=Path, help="STL, OBJ, ASCII PLY, XYZ/PTS, or CSV points.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--sections", type=int, default=20)
    parser.add_argument("--points", type=int, default=7)
    parser.add_argument("--degree", type=int, default=3)
    parser.add_argument("--grid-x", type=int, default=180)
    parser.add_argument("--grid-y", type=int, default=110)
    parser.add_argument("--drop-section", type=int, action="append", default=[])
    args = parser.parse_args()

    pts, tris = load_geometry(args.input)
    if len(pts) < 10:
        raise RuntimeError("Not enough points to fit a surface.")
    mn = pts.min(axis=0)
    mx = pts.max(axis=0)
    base_z = float(mn[2])
    samples = high_surface_samples(pts, mn, mx, base_z, args.grid_x, args.grid_y)
    if len(samples) < 30:
        samples = pts
    coef, kept = fit_surface(samples, mn, mx, args.degree)

    shifted_mn = np.array([mn[0], mn[1], base_z], dtype=np.float64)
    xs = np.linspace(mn[0], mx[0], args.sections)
    ys = np.linspace(mn[1], mx[1], args.points)
    profiles = []
    dropped = set(args.drop_section)
    for si, x in enumerate(xs):
        if si in dropped:
            continue
        zz = eval_surface(coef, np.full_like(ys, x), ys, mn, mx, args.degree)
        zz = np.maximum(zz, base_z + 8.0)
        curve = [{"x": float(x - shifted_mn[0]), "y": float(y - shifted_mn[1]), "z": float(z - shifted_mn[2])} for y, z in zip(ys, zz)]
        profiles.append({"name": f"Section_{si:02d}", "x": float(x - shifted_mn[0]), "curve": curve})

    report = {
        "source": str(args.input),
        "input_stats": mesh_stats(pts, tris),
        "bbox_original": {"min": mn.tolist(), "max": mx.tolist()},
        "bbox_shifted": {"min": [0.0, 0.0, 0.0], "max": (mx - shifted_mn).tolist()},
        "section_count": len(profiles),
        "spline_points_per_section": args.points,
        "fit_samples": int(len(samples)),
        "fit_samples_kept": kept,
        "surface_fit": f"degree-{args.degree} polynomial fitted from high-Z sampled target face",
        "profiles": profiles,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("JSON", args.out)
    print("INPUT_STATS", report["input_stats"])
    print("BBOX_SHIFTED", report["bbox_shifted"])
    print("SAMPLES", len(samples), "KEPT", kept)


if __name__ == "__main__":
    main()
