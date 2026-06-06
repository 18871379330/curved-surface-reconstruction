import argparse
import json
from pathlib import Path

from surface_profiles_from_samples import load_geometry, mesh_stats


def main():
    parser = argparse.ArgumentParser(description="Verify generic mesh/point geometry quality.")
    parser.add_argument("input", type=Path, help="STL, OBJ, ASCII PLY, XYZ/PTS, or CSV points.")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    pts, tris = load_geometry(args.input)
    mn = pts.min(axis=0)
    mx = pts.max(axis=0)
    stats = mesh_stats(pts, tris)
    watertight = stats["open_edges"] == 0 if stats["open_edges"] is not None else None
    manifold = stats["nonmanifold_edges"] == 0 if stats["nonmanifold_edges"] is not None else None
    positive_volume = stats["positive_volume"]
    report = {
        "source": str(args.input),
        "bbox": {"min": mn.tolist(), "max": mx.tolist(), "size": (mx - mn).tolist()},
        "stats": stats,
        "checks": {
            "watertight": watertight,
            "manifold": manifold,
            "positive_volume": positive_volume,
            "point_count_ok": len(pts) >= 10,
        },
    }
    print("GEOMETRY_REPORT", json.dumps(report, ensure_ascii=False))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    failed = [k for k, v in report["checks"].items() if v is False]
    return 0 if not failed else 3


if __name__ == "__main__":
    raise SystemExit(main())
