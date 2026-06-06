import argparse
import json
import math
import struct
from pathlib import Path

import cadquery as cq
import numpy as np
from PIL import Image, ImageDraw


def read_binary_stl(path: Path) -> np.ndarray:
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


def smooth_1d(values, passes=2):
    values = np.asarray(values, dtype=np.float64)
    kernel = np.array([1, 4, 6, 4, 1], dtype=np.float64) / 16.0
    out = values.copy()
    for _ in range(passes):
        out = np.convolve(np.pad(out, (2, 2), mode="edge"), kernel, mode="valid")
    return out


def smooth_2d(values, passes=1):
    out = np.asarray(values, dtype=np.float64).copy()
    for _ in range(passes):
        for i in range(out.shape[0]):
            out[i, :] = smooth_1d(out[i, :], passes=1)
        for j in range(out.shape[1]):
            out[:, j] = smooth_1d(out[:, j], passes=1)
    return out


def quantile_with_window(points, axis, center, half_window, q, min_count=80):
    window = half_window
    mask = np.abs(points[:, axis] - center) <= window
    while mask.sum() < min_count and window < half_window * 8.0:
        window *= 1.35
        mask = np.abs(points[:, axis] - center) <= window
    if mask.sum() == 0:
        return float(np.quantile(points[:, axis], q))
    return float(np.quantile(points[mask, axis], q))


def smoothstep(t):
    return t * t * (3.0 - 2.0 * t)


def scaled_section(section, source_x, origin_x, scale, name):
    all_points = section["back_curve"] + section["front_curve"]
    center_y = float(np.mean([p["y"] for p in all_points]))
    center_z = float(np.mean([p["z"] for p in all_points]))

    def scaled_point(point):
        return {
            "y": float(center_y + (point["y"] - center_y) * scale),
            "z": float(center_z + (point["z"] - center_z) * scale),
        }

    return {
        "name": name,
        "x": float(source_x - origin_x),
        "source_x": float(source_x),
        "back_curve": [scaled_point(p) for p in section["back_curve"]],
        "front_curve": [scaled_point(p) for p in section["front_curve"]],
    }


def append_micro_end_caps(sections, origin_x, source_x_min, source_x_max, cap_sections=4, min_scale=0.04):
    if cap_sections <= 0:
        return sections

    first = sections[0]
    last = sections[-1]
    left_caps = []
    for i in range(cap_sections):
        u = i / float(cap_sections)
        scale = min_scale + (1.0 - min_scale) * smoothstep(u)
        x = source_x_min + (first["source_x"] - source_x_min) * smoothstep(u)
        left_caps.append(scaled_section(first, x, origin_x, scale, f"LeftMicroCap_{i:02d}"))

    right_caps = []
    for i in range(1, cap_sections + 1):
        u = i / float(cap_sections)
        scale = min_scale + (1.0 - min_scale) * (1.0 - smoothstep(u))
        x = last["source_x"] + (source_x_max - last["source_x"]) * smoothstep(u)
        right_caps.append(scaled_section(last, x, origin_x, scale, f"RightMicroCap_{i:02d}"))

    return left_caps + sections + right_caps


def extract_spline_sections(
    points,
    section_count=31,
    z_count=21,
    x_coverage=0.99,
    end_cap_sections=0,
    end_cap_min_scale=0.04,
    x_range_mode="quantile",
    end_cap_extra=0.0,
):
    mn = points.min(axis=0)
    mx = points.max(axis=0)
    size = mx - mn
    origin = np.array([0.5 * (mn[0] + mx[0]), 0.5 * (mn[1] + mx[1]), mn[2]], dtype=np.float64)

    tail = max(0.0, min(0.2, (1.0 - x_coverage) / 2.0))
    source_x_min = float(mn[0])
    source_x_max = float(mx[0])
    cap_x_min = source_x_min - float(end_cap_extra)
    cap_x_max = source_x_max + float(end_cap_extra)
    if x_range_mode == "bbox":
        x_min = float(source_x_min + (source_x_max - source_x_min) * tail)
        x_max = float(source_x_max - (source_x_max - source_x_min) * tail)
    else:
        x_min = float(np.quantile(points[:, 0], tail))
        x_max = float(np.quantile(points[:, 0], 1.0 - tail))
    xs = np.linspace(x_min, x_max, section_count)
    x_half_window = max((x_max - x_min) / max(section_count - 1, 1) * 0.82, 2.5)

    raw = []
    y_back = np.zeros((section_count, z_count), dtype=np.float64)
    y_front = np.zeros((section_count, z_count), dtype=np.float64)
    z_grid = np.zeros((section_count, z_count), dtype=np.float64)
    z_low = np.zeros(section_count, dtype=np.float64)
    z_high = np.zeros(section_count, dtype=np.float64)

    for si, x in enumerate(xs):
        window = x_half_window
        mask = np.abs(points[:, 0] - x) <= window
        while mask.sum() < 1600 and window < size[0] * 0.12:
            window *= 1.35
            mask = np.abs(points[:, 0] - x) <= window
        section = points[mask]
        if len(section) == 0:
            section = points

        z_low[si] = np.quantile(section[:, 2], 0.018)
        z_high[si] = np.quantile(section[:, 2], 0.982)
        raw.append(
            {
                "x": float(x),
                "sample_count": int(len(section)),
                "window": float(window),
                "z_low_raw": float(z_low[si]),
                "z_high_raw": float(z_high[si]),
            }
        )

    z_low = smooth_1d(z_low, passes=2)
    z_high = smooth_1d(z_high, passes=2)

    for si, x in enumerate(xs):
        window = x_half_window
        mask = np.abs(points[:, 0] - x) <= window
        while mask.sum() < 1600 and window < size[0] * 0.12:
            window *= 1.35
            mask = np.abs(points[:, 0] - x) <= window
        section = points[mask]
        if len(section) == 0:
            section = points

        zs = np.linspace(z_low[si], z_high[si], z_count)
        dz = max((z_high[si] - z_low[si]) / max(z_count - 1, 1) * 0.92, 4.0)
        z_grid[si, :] = zs

        for zi, z in enumerate(zs):
            local = section[np.abs(section[:, 2] - z) <= dz]
            if len(local) < 80:
                local = section[np.abs(section[:, 2] - z) <= dz * 1.8]
            if len(local) < 25:
                local = section
            y_back[si, zi] = np.quantile(local[:, 1], 0.035)
            y_front[si, zi] = np.quantile(local[:, 1], 0.965)

    y_back = smooth_2d(y_back, passes=2)
    y_front = smooth_2d(y_front, passes=2)

    min_thickness = max(8.0, size[1] * 0.055)
    for si in range(section_count):
        for zi in range(z_count):
            if y_front[si, zi] - y_back[si, zi] < min_thickness:
                center = 0.5 * (y_front[si, zi] + y_back[si, zi])
                y_back[si, zi] = center - min_thickness / 2.0
                y_front[si, zi] = center + min_thickness / 2.0

    sections = []
    for si, x in enumerate(xs):
        sections.append(
            {
                "name": f"SplineSection_{si:02d}",
                "x": float(x - origin[0]),
                "source_x": float(x),
                "back_curve": [
                    {"y": float(y_back[si, zi] - origin[1]), "z": float(z_grid[si, zi] - origin[2])}
                    for zi in range(z_count)
                ],
                "front_curve": [
                    {"y": float(y_front[si, zi] - origin[1]), "z": float(z_grid[si, zi] - origin[2])}
                    for zi in range(z_count)
                ],
            }
        )

    sections = append_micro_end_caps(
        sections,
        float(origin[0]),
        cap_x_min,
        cap_x_max,
        cap_sections=end_cap_sections,
        min_scale=end_cap_min_scale,
    )

    return {
        "reference_bbox": {"min": mn.tolist(), "max": mx.tolist(), "size": size.tolist()},
        "origin_shift": {"x": float(origin[0]), "y": float(origin[1]), "z": float(origin[2])},
        "section_count": section_count,
        "total_section_count_with_caps": len(sections),
        "z_points_per_side": z_count,
        "x_coverage": float(x_coverage),
        "x_tail_each_side": float(tail),
        "x_sample_range": [float(x_min), float(x_max)],
        "x_source_range": [source_x_min, source_x_max],
        "x_cap_range": [cap_x_min, cap_x_max],
        "x_range_mode": x_range_mode,
        "end_cap_extra": float(end_cap_extra),
        "end_cap_sections": int(end_cap_sections),
        "end_cap_min_scale": float(end_cap_min_scale),
        "raw_section_sampling": raw,
        "sections": sections,
    }


def vector(x, point):
    return cq.Vector(x, point["y"], point["z"])


def clean_points(points, min_dist=0.06):
    cleaned = []
    for p in points:
        if not cleaned or (p - cleaned[-1]).Length > min_dist:
            cleaned.append(p)
    return cleaned


def make_spline_or_line(points):
    pts = clean_points(points)
    if len(pts) < 2:
        raise RuntimeError("Not enough points for profile edge")
    if len(pts) == 2:
        return cq.Edge.makeLine(pts[0], pts[1])
    try:
        return cq.Edge.makeSpline(pts, tol=1e-4)
    except Exception:
        keep = pts[::2]
        if keep[-1] != pts[-1]:
            keep.append(pts[-1])
        if len(keep) <= 2:
            return cq.Edge.makeLine(pts[0], pts[-1])
        return cq.Edge.makeSpline(keep, tol=1e-3)


def make_wire(section):
    x = section["x"]
    back = [vector(x, p) for p in section["back_curve"]]
    front = [vector(x, p) for p in section["front_curve"]]

    back_edge = make_spline_or_line(back)
    top_edge = make_spline_or_line([back[-1], (back[-1] + front[-1]) * 0.5 + cq.Vector(0, 0, 2.0), front[-1]])
    front_edge = make_spline_or_line(list(reversed(front)))
    bottom_edge = make_spline_or_line([front[0], (front[0] + back[0]) * 0.5 - cq.Vector(0, 0, 2.0), back[0]])
    return cq.Wire.assembleEdges([back_edge, top_edge, front_edge, bottom_edge])


def build_solid(profile, fillet_radius=0.0):
    wires = [make_wire(section) for section in profile["sections"]]
    solid = cq.Solid.makeLoft(wires, ruled=False)
    if solid is None:
        raise RuntimeError("CadQuery loft returned None")
    if not solid.isValid():
        raise RuntimeError("CadQuery loft solid is invalid")
    if fillet_radius > 0:
        try:
            bbox = solid.BoundingBox()
            tol = max((bbox.xmax - bbox.xmin) * 0.002, 0.5)
            end_edges = [
                edge
                for edge in solid.Edges()
                if abs(edge.Center().x - bbox.xmin) <= tol or abs(edge.Center().x - bbox.xmax) <= tol
            ]
            filleted = solid.fillet(fillet_radius, end_edges)
            if filleted is not None and filleted.isValid():
                solid = filleted
        except Exception as exc:
            print("FILLET_SKIPPED", fillet_radius, repr(exc))
    return solid


def rotation_matrix(ax, ay, az):
    ax, ay, az = [math.radians(v) for v in (ax, ay, az)]
    rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), math.cos(ay), 0]])
    # Correct the Y rotation matrix explicitly; keep this helper local to previews.
    ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
    rz = np.array([[math.cos(az), -math.sin(az), 0], [math.sin(az), math.cos(az), 0], [0, 0, 1]])
    return rz @ ry @ rx


def render_triangles(tris, title, width, height, angles):
    img = Image.new("RGB", (width, height), (246, 248, 252))
    draw = ImageDraw.Draw(img)
    pts = tris.reshape(-1, 3)
    center = 0.5 * (pts.min(axis=0) + pts.max(axis=0))
    rotated = (pts - center) @ rotation_matrix(*angles).T
    proj = rotated[:, :2]
    mins = proj.min(axis=0)
    maxs = proj.max(axis=0)
    scale = min((width - 64) / max(maxs[0] - mins[0], 1e-9), (height - 72) / max(maxs[1] - mins[1], 1e-9))
    xy = (proj - 0.5 * (mins + maxs)) * scale
    xy[:, 0] += width / 2
    xy[:, 1] = height / 2 - xy[:, 1] + 14
    rtris = rotated.reshape(-1, 3, 3)
    xytris = xy.reshape(-1, 3, 2)
    order = np.argsort(rtris[:, :, 2].mean(axis=1))
    light = np.array([0.25, -0.45, 0.86], dtype=np.float64)
    light /= np.linalg.norm(light)
    for tri_idx in order:
        tri = rtris[tri_idx]
        normal = np.cross(tri[1] - tri[0], tri[2] - tri[0])
        norm = np.linalg.norm(normal)
        shade = 0.60
        if norm > 1e-9:
            normal /= norm
            shade = max(0.28, min(0.96, 0.60 + 0.34 * float(np.dot(normal, light))))
        color = tuple(int(205 * shade + 32) for _ in range(3))
        draw.polygon([tuple(p) for p in xytris[tri_idx]], fill=color)
    draw.rectangle((0, 0, width - 1, height - 1), outline=(205, 212, 224))
    draw.text((14, 12), title, fill=(22, 28, 36))
    return img


def render_preview(stl_path: Path, out_path: Path):
    tris = read_binary_stl(stl_path)
    views = [("ISO", (-22, 0, 35)), ("FRONT", (0, 0, 0)), ("SIDE", (0, 0, 90)), ("TOP", (90, 0, 0))]
    tile_w, tile_h = 520, 390
    sheet = Image.new("RGB", (tile_w * 2, tile_h * 2), (255, 255, 255))
    for idx, (name, angles) in enumerate(views):
        sheet.paste(render_triangles(tris, name, tile_w, tile_h, angles), ((idx % 2) * tile_w, (idx // 2) * tile_h))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-stl", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--basename", default="h3_audi_spline_fitted_pillow_single_solid")
    parser.add_argument("--sections", type=int, default=31)
    parser.add_argument("--z-points", type=int, default=23)
    parser.add_argument("--x-coverage", type=float, default=0.99)
    parser.add_argument("--end-cap-sections", type=int, default=0)
    parser.add_argument("--end-cap-min-scale", type=float, default=0.04)
    parser.add_argument("--fillet-radius", type=float, default=0.0)
    parser.add_argument("--x-range-mode", choices=["quantile", "bbox"], default="quantile")
    parser.add_argument("--end-cap-extra", type=float, default=0.0)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    tris = read_binary_stl(args.reference_stl)
    points = tris.reshape(-1, 3)
    profile = extract_spline_sections(
        points,
        args.sections,
        args.z_points,
        x_coverage=args.x_coverage,
        end_cap_sections=args.end_cap_sections,
        end_cap_min_scale=args.end_cap_min_scale,
        x_range_mode=args.x_range_mode,
        end_cap_extra=args.end_cap_extra,
    )
    profile["reference_stl"] = str(args.reference_stl)
    profile["method"] = "closed spline section loft from STL y-min/y-max section profiles"

    profile["edge_fillet_radius"] = float(args.fillet_radius)

    solid = build_solid(profile, fillet_radius=args.fillet_radius)
    step_path = args.out_dir / f"{args.basename}.step"
    stl_path = args.out_dir / f"{args.basename}_preview.stl"
    preview_path = args.out_dir / f"{args.basename}_preview.png"
    profile_path = args.out_dir / f"{args.basename}_profiles.json"
    report_path = args.out_dir / f"{args.basename}_validation.json"

    cq.exporters.export(solid, str(step_path))
    cq.exporters.export(solid, str(stl_path), tolerance=0.08, angularTolerance=0.08)
    render_preview(stl_path, preview_path)

    reopened = cq.importers.importStep(str(step_path)).solids().vals()
    report = {
        "valid": bool(solid.isValid()),
        "volume_mm3": float(solid.Volume()),
        "face_count": int(len(solid.Faces())),
        "solid_count": int(len(cq.Compound.makeCompound([solid]).Solids())),
        "step_reopen_solid_count": int(len(reopened)),
        "step_reopen_valid": bool(reopened[0].isValid()) if reopened else False,
        "outputs": {
            "step": str(step_path),
            "preview_stl": str(stl_path),
            "preview_png": str(preview_path),
            "profiles": str(profile_path),
        },
    }
    profile_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("VALID", report["valid"])
    print("VOLUME_MM3", report["volume_mm3"])
    print("FACES", report["face_count"])
    print("SOLIDS", report["solid_count"])
    print("STEP_REOPEN_SOLIDS", report["step_reopen_solid_count"])
    print("STEP_REOPEN_VALID", report["step_reopen_valid"])
    print("STEP", step_path)
    print("STL", stl_path)
    print("PREVIEW", preview_path)
    print("PROFILE_JSON", profile_path)
    print("REPORT", report_path)


if __name__ == "__main__":
    main()
