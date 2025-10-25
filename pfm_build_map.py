#!/usr/bin/env python3
"""
pfm_build_map.py

Utility script to generate a pfm.json-style font map
from the system's fontconfig database (`fc-list`).

Usage:
    python pfm_build_map.py > pfm.json
    python pfm_build_map.py --filter "Futura|Helvetica|Hiragino" > pfm.json

This is meant to help teams bootstrap PlotFontManager by
auto-creating a logical-name -> font-file mapping.
Edit the resulting JSON and keep only the fonts you actually care about
(you probably don't want 500 entries in version control).
"""

import subprocess
import json
import re
import argparse
from collections import OrderedDict
from pathlib import Path


def collect_fc_list():
    """
    Run `fc-list` to get installed fonts.
    We ask for "file:family" per line.

    Returns:
        list[tuple[str, str]]
        Each entry is (filepath, family_name)
    """
    try:
        # -f "%{file}:%{family}\n" gives absolute path and the family list
        result = subprocess.run(
            ["fc-list", "-f", "%{file}:%{family}\n"],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "fc-list not found. Please install fontconfig (e.g. `fc-list` command)."
        )

    lines = result.stdout.splitlines()
    out = []

    for line in lines:
        if ":" not in line:
            continue
        path, family = line.split(":", 1)

        # family might be "Helvetica Neue,HelveticaNeue DeskInterface"
        # so pick the first "canonical-looking" one
        first_family = family.split(",")[0].strip()

        # normalize weird whitespace
        first_family = re.sub(r"\s+", " ", first_family)

        # basic sanity check: skip empty names
        if not first_family:
            continue

        out.append((path.strip(), first_family))

    return out


def build_map(entries, family_filter=None):
    """
    Build an OrderedDict mapping logical font name -> font file path.

    Args:
        entries: list[(path, family)]
        family_filter: compiled regex or None

    Behavior:
        - The first occurrence of a given family wins.
        - If family_filter is provided, only families that match are kept.

    Returns:
        OrderedDict[str, str]
    """
    mapping = OrderedDict()

    for path, fam in entries:
        if family_filter and not family_filter.search(fam):
            continue
        if fam not in mapping:
            # store absolute path as string
            mapping[fam] = str(Path(path).resolve())

    return mapping


def main():
    parser = argparse.ArgumentParser(
        description="Generate pfm.json mapping from `fc-list`."
    )
    parser.add_argument(
        "--filter",
        type=str,
        default=None,
        help="Regex to filter family names (e.g. 'Futura|Helvetica|Hiragino').",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=4,
        help="Indent level for JSON output (default: 4).",
    )
    args = parser.parse_args()

    family_filter = re.compile(args.filter) if args.filter else None

    entries = collect_fc_list()
    mapping = build_map(entries, family_filter=family_filter)

    # Dump JSON to stdout
    print(json.dumps(mapping, ensure_ascii=False, indent=args.indent))


if __name__ == "__main__":
    main()
