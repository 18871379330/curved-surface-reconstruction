import argparse
import csv
import json
import math
import struct
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


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
    return tris


def read_ascii_stl(path: Path):
    verts = []
    tris = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.strip().split()
        if len(parts) == 4 and parts[0].lower() == "vertex":
            verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
            if len(verts) == 3:
                tris.append(verts)
                verts = []
    return np.asarray(tris, dtype=np.float64) if tris else np.zeros((0, 3, 3), dtype=np.float64)


def read_stl(path: Path):
    size = path.stat().st_size
    if size >= 84:
        with path.open("rb") as fh:
            header = fh.read(80)
            count = struct.unpack("<I", fh.read(4))[0]
        if 84 + count * 50 == size or not header[:5].lower().startswith(b"solid"):
            return read_binary_stl(path)
    return read_ascii_stl(path)


def read_obj_as_tris(path: Path):
    verts = []
    tris = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("v "):
            parts = line.split()
            verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
        elif line.startswith("f "):
            idx = []
            for token in line.split()[1:]:
                raw = int(token.split("/")[0])
                idx.append(raw - 1 if raw > 0 else len(verts) + raw)
            for i in range(1, len(idx) - 1):
                tris.append([verts[idx[0]], verts[idx[i]], verts[idx[i + 1]]])
    return np.asarray(tris, dtype=np.float64)


def read_mesh(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".stl":
        return read_stl(path)
    if suffix == ".obj":
        return read_obj_as_tris(path)
    raise ValueError(f"Unsupported mesh format for scene inspection: {suffix}")


def triangle_area(tris):
    if len(tris) == 0:
        return 0.0
    return float(0.5 * np.linalg.norm(np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]), axis=1).sum())


def signed_volume(tris):
    if len(tris) == 0:
        return 0.0
    return float(np.einsum("ij,ij->i", tris[:, 0], np.cross(tris[:, 1], tris[:, 2])).sum() / 6.0)


def topology_metrics(tris, weld_tolerance=1e-6):
    metrics = {
        "unique_vertices": 0,
        "open_edges": None,
        "nonmanifold_edges": None,
        "degenerate_faces": None,
    }
    if len(tris) == 0:
        return metrics
    key_to_idx = {}
    edge_counts = defaultdict(int)
    degenerate = 0
    for tri in tris:
        face = []
        for point in tri:
            key = tuple(np.round(point / weld_tolerance).astype(np.int64))
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
    metrics.update({
        "unique_vertices": int(len(key_to_idx)),
        "open_edges": int(sum(count == 1 for count in edge_counts.values())),
        "nonmanifold_edges": int(sum(count > 2 for count in edge_counts.values())),
        "degenerate_faces": int(degenerate),
    })
    return metrics


def aspect_metrics(size):
    ordered = np.sort(np.maximum(size, 1e-9))[::-1]
    return {
        "long_mid_ratio": float(ordered[0] / ordered[1]),
        "long_short_ratio": float(ordered[0] / ordered[2]),
        "flatness_ratio": float(ordered[2] / ordered[0]),
    }


def choose_file_variants(files, keep_duplicates=False):
    if keep_duplicates:
        return sorted(files, key=lambda p: str(p).lower())
    groups = defaultdict(list)
    for path in files:
        groups[(str(path.parent).lower(), path.stem.lower())].append(path)
    chosen = []
    priority = {".stl": 0, ".obj": 1}
    for group in groups.values():
        chosen.append(sorted(group, key=lambda p: (priority.get(p.suffix.lower(), 9), str(p).lower()))[0])
    return sorted(chosen, key=lambda p: str(p).lower())


def split_connected_components(tris, weld_tolerance=1e-5):
    if len(tris) == 0:
        return []
    parent = list(range(len(tris)))

    def find(item):
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a, b):
        ra = find(a)
        rb = find(b)
        if ra != rb:
            parent[rb] = ra

    owner_by_vertex = {}
    for tri_idx, tri in enumerate(tris):
        for point in tri:
            key = tuple(np.round(point / weld_tolerance).astype(np.int64))
            owner = owner_by_vertex.get(key)
            if owner is None:
                owner_by_vertex[key] = tri_idx
            else:
                union(tri_idx, owner)

    groups = defaultdict(list)
    for tri_idx in range(len(tris)):
        groups[find(tri_idx)].append(tri_idx)
    return sorted((np.asarray(indices, dtype=np.int64) for indices in groups.values()), key=len, reverse=True)


def classify_component(summary, scene):
    tri_ratio = summary["triangles"] / max(scene["max_triangles"], 1)
    volume_ratio = summary["bbox_volume"] / max(scene["max_bbox_volume"], 1e-9)
    area_ratio = summary["surface_area"] / max(scene["max_surface_area"], 1e-9)
    diag_ratio = summary["bbox_diag"] / max(scene["bbox_diag"], 1e-9)
    scene_size = np.maximum(np.asarray(scene["bbox_size"], dtype=np.float64), 1e-9)
    large_span_axes = int(np.sum(np.asarray(summary["bbox_size"], dtype=np.float64) / scene_size >= 0.55))
    long_short = summary["long_short_ratio"]
    flatness = summary["flatness_ratio"]
    area_density = summary["surface_area_to_bbox_diag2"]
    volume_fill = summary["abs_volume_to_bbox_volume"]
    size = summary["bbox_size"]

    reasons = []
    risk_notes = []
    if tri_ratio >= 0.45 or volume_ratio >= 0.45:
        reasons.append("large component")
    if long_short >= 15.0:
        reasons.append("very high aspect ratio")
        risk_notes.append("can be a strap/ribbon/detail if not part of the intended body")
    if flatness <= 0.045:
        reasons.append("thin/flat component")
        risk_notes.append("thin sheets often represent seams, bands, panels, or scan fragments")
    if summary["triangles"] <= max(2000, scene["max_triangles"] * 0.06):
        reasons.append("small triangle count")
        risk_notes.append("small components are usually details unless design intent says otherwise")
    if min(size) <= max(scene["bbox_diag"] * 0.025, 1e-9):
        reasons.append("thin bbox axis")
    if large_span_axes >= 2:
        reasons.append("large scene span")
    if diag_ratio >= 0.35 and area_density <= 0.08:
        reasons.append("low surface area for bbox span")
        risk_notes.append("wire loops, stitching, tubes, and sparse frames can have many triangles but little surface mass")
    if diag_ratio >= 0.35 and volume_fill <= 0.04:
        reasons.append("very low bbox volume fill")
        risk_notes.append("low fill relative to bbox often means a strap, open frame, loop, or non-body detail")

    size_score = (
        0.32 * min(tri_ratio / 0.45, 1.0)
        + 0.28 * min(volume_ratio / 0.45, 1.0)
        + 0.24 * min(area_ratio / 0.45, 1.0)
        + 0.10 * min(diag_ratio / 0.65, 1.0)
        + 0.06 * min(large_span_axes / 2.0, 1.0)
    )
    risk_penalty = 0.0
    if long_short >= 15.0:
        risk_penalty += 0.25
    if flatness <= 0.045:
        risk_penalty += 0.25
    if summary["triangles"] <= max(2000, scene["max_triangles"] * 0.06):
        risk_penalty += 0.16
    if min(size) <= max(scene["bbox_diag"] * 0.025, 1e-9):
        risk_penalty += 0.10
    if diag_ratio >= 0.35 and area_density <= 0.08:
        risk_penalty += 0.30
    if diag_ratio >= 0.35 and volume_fill <= 0.04:
        risk_penalty += 0.25
    main_body_score = max(0.0, min(1.0, size_score - risk_penalty))

    strong_detail_risk = (
        "very high aspect ratio" in reasons
        or "thin/flat component" in reasons
        or "low surface area for bbox span" in reasons
        or "very low bbox volume fill" in reasons
    )

    if main_body_score >= 0.68 and not strong_detail_risk:
        label = "main_body_candidate"
        recommendation = "include_for_review"
    elif main_body_score >= 0.45:
        label = "review_surface_candidate"
        recommendation = "review_before_include"
    elif strong_detail_risk:
        label = "accessory_or_detail_candidate"
        recommendation = "exclude_unless_requested"
    elif "small triangle count" in reasons:
        label = "detail_candidate"
        recommendation = "exclude_unless_requested"
    else:
        label = "secondary_surface_candidate"
        recommendation = "review_before_include"

    return label, reasons, risk_notes, main_body_score, recommendation


def summarize_tris(path: Path, name, tris, component_index=None, component_count=None):
    pts = tris.reshape(-1, 3) if len(tris) else np.zeros((0, 3), dtype=np.float64)
    if len(pts) == 0:
        mn = mx = size = np.zeros(3, dtype=np.float64)
    else:
        mn = pts.min(axis=0)
        mx = pts.max(axis=0)
        size = mx - mn
    metrics = aspect_metrics(size)
    bbox_volume = float(np.prod(np.maximum(size, 0.0)))
    topo = topology_metrics(tris)
    summary = {
        "path": str(path),
        "source_file": path.name,
        "name": name,
        "component_index": component_index,
        "component_count": component_count,
        "triangles": int(len(tris)),
        "points": int(len(pts)),
        "bbox_min": mn.tolist(),
        "bbox_max": mx.tolist(),
        "bbox_size": size.tolist(),
        "bbox_diag": float(np.linalg.norm(size)),
        "bbox_volume": bbox_volume,
        "surface_area": triangle_area(tris),
        "signed_volume": signed_volume(tris),
        **metrics,
        **topo,
    }
    summary["abs_volume_to_bbox_volume"] = float(abs(summary["signed_volume"]) / max(bbox_volume, 1e-9))
    summary["surface_area_to_bbox_diag2"] = float(summary["surface_area"] / max(summary["bbox_diag"] ** 2, 1e-9))
    return summary


def summarize_file(path: Path, split_components=False, weld_tolerance=1e-5, min_component_triangles=1):
    tris = read_mesh(path)
    if not split_components:
        return [(summarize_tris(path, path.name, tris), tris)]

    components = split_connected_components(tris, weld_tolerance=weld_tolerance)
    kept = [indices for indices in components if len(indices) >= min_component_triangles]
    if not kept:
        return [(summarize_tris(path, path.name, tris), tris)]

    result = []
    component_count = len(kept)
    for idx, indices in enumerate(kept, start=1):
        comp_tris = tris[indices]
        name = f"{path.stem}#cc{idx:03d}{path.suffix.lower()}"
        result.append((summarize_tris(path, name, comp_tris, idx, component_count), comp_tris))
    return result


def rotation_matrix(ax=-25, ay=0, az=35):
    ax, ay, az = [math.radians(v) for v in (ax, ay, az)]
    rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
    rz = np.array([[math.cos(az), -math.sin(az), 0], [math.sin(az), math.cos(az), 0], [0, 0, 1]])
    return rz @ ry @ rx


def render_component(tris, summary, width=420, height=320, max_triangles=60000):
    img = Image.new("RGB", (width, height), (246, 248, 252))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, width - 1, height - 1), outline=(205, 212, 224))
    if len(tris) == 0:
        draw.text((12, 12), summary["name"], fill=(120, 0, 0))
        return img

    stride = max(1, len(tris) // max_triangles)
    sample = tris[::stride]
    pts = sample.reshape(-1, 3)
    center = 0.5 * (pts.min(axis=0) + pts.max(axis=0))
    r = rotation_matrix()
    rotated = (pts - center) @ r.T
    proj = rotated[:, :2]
    mn = proj.min(axis=0)
    mx = proj.max(axis=0)
    scale = min((width - 52) / max(mx[0] - mn[0], 1e-9), (height - 72) / max(mx[1] - mn[1], 1e-9))
    xy = (proj - 0.5 * (mn + mx)) * scale
    xy[:, 0] += width / 2
    xy[:, 1] = height / 2 - xy[:, 1] + 14
    rtris = rotated.reshape(-1, 3, 3)
    xytris = xy.reshape(-1, 3, 2)
    order = np.argsort(rtris[:, :, 2].mean(axis=1))
    light = np.array([0.25, -0.45, 0.86], dtype=np.float64)
    light /= np.linalg.norm(light)
    for idx in order:
        tri = rtris[idx]
        normal = np.cross(tri[1] - tri[0], tri[2] - tri[0])
        norm = np.linalg.norm(normal)
        shade = 0.58
        if norm > 1e-9:
            normal /= norm
            shade = max(0.24, min(0.96, 0.58 + 0.34 * float(np.dot(normal, light))))
        color = tuple(int(205 * shade + 32) for _ in range(3))
        draw.polygon([tuple(p) for p in xytris[idx]], fill=color)

    label = f"{summary['name']} | {summary['classification']}"
    draw.text((12, 10), label[:78], fill=(20, 24, 32))
    draw.text((12, height - 24), f"tris {summary['triangles']}  L/S {summary['long_short_ratio']:.1f}", fill=(70, 78, 92))
    return img


def write_tsv(path: Path, summaries):
    fields = [
        "name",
        "source_file",
        "component_index",
        "component_count",
        "classification",
        "main_body_score",
        "recommendation",
        "triangles",
        "points",
        "unique_vertices",
        "open_edges",
        "nonmanifold_edges",
        "degenerate_faces",
        "bbox_min",
        "bbox_max",
        "bbox_size",
        "bbox_diag",
        "abs_volume_to_bbox_volume",
        "surface_area_to_bbox_diag2",
        "long_mid_ratio",
        "long_short_ratio",
        "flatness_ratio",
        "surface_area",
        "signed_volume",
        "classification_reasons",
        "risk_notes",
        "path",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for summary in summaries:
            row = dict(summary)
            for key in ("bbox_min", "bbox_max", "bbox_size", "classification_reasons", "risk_notes"):
                row[key] = ",".join(str(x) for x in row[key])
            writer.writerow({key: row.get(key, "") for key in fields})


def write_contact_sheet(path: Path, summaries, meshes, columns=3):
    if not summaries:
        return
    thumbs = [render_component(mesh, summary) for summary, mesh in zip(summaries, meshes)]
    tile_w, tile_h = thumbs[0].size
    rows = (len(thumbs) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile_w, rows * tile_h), (255, 255, 255))
    for idx, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((idx % columns) * tile_w, (idx // columns) * tile_h))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def main():
    parser = argparse.ArgumentParser(description="Inspect a mesh scene before curved-surface reconstruction.")
    parser.add_argument("inputs", type=Path, nargs="+", help="STL/OBJ files, or directories containing STL/OBJ files.")
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-tsv", type=Path)
    parser.add_argument("--contact-sheet", type=Path)
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--keep-format-duplicates", action="store_true", help="Keep same-stem STL/OBJ pairs instead of preferring STL.")
    parser.add_argument("--split-components", action="store_true", help="Split each mesh into welded connected triangle components before classification.")
    parser.add_argument("--weld-tolerance", type=float, default=1e-5)
    parser.add_argument("--min-component-triangles", type=int, default=20)
    args = parser.parse_args()

    files = []
    for input_path in args.inputs:
        if input_path.is_dir():
            pattern = "**/*" if args.recursive else "*"
            files.extend([p for p in input_path.glob(pattern) if p.suffix.lower() in {".stl", ".obj"}])
        elif input_path.suffix.lower() in {".stl", ".obj"}:
            files.append(input_path)
    files = choose_file_variants(dict.fromkeys(files), keep_duplicates=args.keep_format_duplicates)
    if not files:
        raise RuntimeError("No STL/OBJ files found for scene inspection.")

    raw = []
    meshes = []
    for path in files:
        for summary, tris in summarize_file(
            path,
            split_components=args.split_components,
            weld_tolerance=args.weld_tolerance,
            min_component_triangles=args.min_component_triangles,
        ):
            raw.append(summary)
            meshes.append(tris)

    all_pts = np.vstack([mesh.reshape(-1, 3) for mesh in meshes if len(mesh)])
    scene_mn = all_pts.min(axis=0)
    scene_mx = all_pts.max(axis=0)
    scene_size = scene_mx - scene_mn
    scene = {
        "file_count": len(files),
        "bbox_min": scene_mn.tolist(),
        "bbox_max": scene_mx.tolist(),
        "bbox_size": scene_size.tolist(),
        "bbox_diag": float(np.linalg.norm(scene_size)),
        "max_triangles": max(item["triangles"] for item in raw),
        "max_bbox_volume": max(item["bbox_volume"] for item in raw),
        "max_surface_area": max(item["surface_area"] for item in raw),
        "split_components": bool(args.split_components),
        "format_duplicates_kept": bool(args.keep_format_duplicates),
    }

    summaries = []
    for summary in raw:
        label, reasons, risk_notes, main_body_score, recommendation = classify_component(summary, scene)
        summary["classification"] = label
        summary["classification_reasons"] = reasons
        summary["risk_notes"] = risk_notes
        summary["main_body_score"] = round(float(main_body_score), 4)
        summary["recommendation"] = recommendation
        summaries.append(summary)

    report = {"scene": scene, "components": summaries}
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.out_tsv:
        write_tsv(args.out_tsv, summaries)
    if args.contact_sheet:
        write_contact_sheet(args.contact_sheet, summaries, meshes)

    print("SCENE_INSPECTION", args.out_json)
    print("COMPONENTS", len(summaries))
    print("MAIN_BODY_CANDIDATES", sum(s["classification"] == "main_body_candidate" for s in summaries))
    if args.out_tsv:
        print("TSV", args.out_tsv)
    if args.contact_sheet:
        print("CONTACT_SHEET", args.contact_sheet)


if __name__ == "__main__":
    main()
