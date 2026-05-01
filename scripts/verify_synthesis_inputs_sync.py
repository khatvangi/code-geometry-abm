#!/usr/bin/env python3
"""
Verify synthesis/inputs/from_nitrogen/ matches its upstream source.

The synthesis pipeline reads inputs from a tracked snapshot at
synthesis/inputs/from_nitrogen/. The authoritative source for those
inputs is the sibling repo at
../violence-abrahamic/data/exports/synthesis_phase_s1/.

This script hashes every file in the snapshot and compares against the
corresponding file upstream. It reports four categories:

  IDENTICAL       file present in both locations, sha256 matches
  CONTENT_DRIFT   file present in both, sha256 differs
  ONLY_IN_SNAP    file in snapshot but not upstream
  ONLY_IN_UPSTR   file in upstream but not snapshot

Default exit codes:
  0 — all files identical or only-snapshot (no drift requiring action)
  1 — content drift or upstream-only files detected
  2 — upstream directory not found (sibling repo absent)

With --strict, exit 1 also if there are ONLY_IN_SNAP files. Without
--strict, those are warnings (since standalone clones of code-geometry-abm
legitimately lack the sibling repo).

With --quiet, suppresses IDENTICAL output; only differences are printed.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
SNAPSHOT_DIR = REPO_ROOT / "synthesis" / "inputs" / "from_nitrogen"
UPSTREAM_DIR = REPO_ROOT.parent / "violence-abrahamic" / "data" / "exports" / "synthesis_phase_s1"


def sha256_of(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def list_files(directory: pathlib.Path) -> dict[str, pathlib.Path]:
    """Return relative-path -> absolute-path map. Skips dotfiles, __pycache__, *.pyc."""
    out: dict[str, pathlib.Path] = {}
    if not directory.exists():
        return out
    for p in directory.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(directory)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if "__pycache__" in rel.parts:
            continue
        if p.suffix in (".pyc", ".pyo"):
            continue
        out[str(rel)] = p
    return out


def verify(strict: bool, quiet: bool) -> int:
    if not UPSTREAM_DIR.exists():
        print(
            f"UPSTREAM ABSENT: {UPSTREAM_DIR} does not exist.\n"
            f"  This is expected in standalone clones of code-geometry-abm.\n"
            f"  Sync verification is only meaningful when the sibling repo\n"
            f"  violence-abrahamic is checked out alongside this one.",
            file=sys.stderr,
        )
        return 2

    snapshot = list_files(SNAPSHOT_DIR)
    upstream = list_files(UPSTREAM_DIR)

    identical: list[str] = []
    drifted: list[tuple[str, str, str]] = []
    only_snap: list[str] = []
    only_upstr: list[str] = []

    all_files = sorted(set(snapshot) | set(upstream))
    for rel in all_files:
        in_snap = rel in snapshot
        in_upstr = rel in upstream
        if in_snap and in_upstr:
            sh_snap = sha256_of(snapshot[rel])
            sh_upstr = sha256_of(upstream[rel])
            if sh_snap == sh_upstr:
                identical.append(rel)
            else:
                drifted.append((rel, sh_snap, sh_upstr))
        elif in_snap:
            only_snap.append(rel)
        else:
            only_upstr.append(rel)

    if not quiet:
        for rel in identical:
            print(f"  IDENTICAL     {rel}")
    for rel, sh_s, sh_u in drifted:
        print(f"  CONTENT_DRIFT {rel}")
        print(f"      snapshot: {sh_s}")
        print(f"      upstream: {sh_u}")
    for rel in only_snap:
        print(f"  ONLY_IN_SNAP  {rel}")
    for rel in only_upstr:
        print(f"  ONLY_IN_UPSTR {rel}  -- run sync (Stage-2 protocol) to incorporate")

    print()
    print(
        f"summary: {len(identical)} identical, "
        f"{len(drifted)} content-drift, "
        f"{len(only_snap)} only-in-snapshot, "
        f"{len(only_upstr)} only-in-upstream"
    )

    has_drift = len(drifted) > 0 or len(only_upstr) > 0
    has_extra = len(only_snap) > 0
    if has_drift:
        print(
            "VERDICT: DRIFT — synthesis/inputs/from_nitrogen/ is out of sync with upstream.\n"
            "         Run the Stage-2 sync protocol to update.",
            file=sys.stderr,
        )
        return 1
    if strict and has_extra:
        print(
            "VERDICT: EXTRA — snapshot has files not in upstream (--strict mode).",
            file=sys.stderr,
        )
        return 1
    print("VERDICT: SYNC_VERIFIED — snapshot matches upstream.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify synthesis/inputs/from_nitrogen/ matches upstream."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail (exit 1) on snapshot-only files in addition to drift.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print mismatches; suppress IDENTICAL lines.",
    )
    args = parser.parse_args()
    return verify(strict=args.strict, quiet=args.quiet)


if __name__ == "__main__":
    sys.exit(main())
