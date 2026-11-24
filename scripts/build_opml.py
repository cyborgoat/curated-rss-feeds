#!/usr/bin/env python3
"""Build the OPML subscription lists from the Markdown catalog."""

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
HEADER = ["Name", "Website", "Feed", "Format", "Language", "Description"]
FORMATS = {"RSS", "Atom", "RDF"}
LINK = re.compile(r"\[[^\]]+\]\((?:<([^<>\s]+)>|([^<>\s]+))\)")


@dataclass(frozen=True)
class Feed:
    name: str
    website: str
    url: str


def table_cells(line):
    if not line.startswith("|") or not line.endswith("|"):
        return []
    return [cell.strip().replace(r"\|", "|") for cell in re.split(r"(?<!\\)\|", line[1:-1])]


def read_link(cell, location):
    match = LINK.fullmatch(cell)
    if not match:
        raise ValueError(f"{location}: expected a Markdown link in {cell!r}")
    url = match[1] or match[2]
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as error:
        raise ValueError(f"{location}: invalid URL {url!r}") from error
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username is not None:
        raise ValueError(f"{location}: expected a public HTTP(S) URL, got {url!r}")
    default_port = 443 if parts.scheme == "https" else 80
    key = (parts.scheme, parts.hostname.lower(), port if port != default_port else None,
           parts.path or "/", parts.query)
    return url, key


def read_category(path, seen_urls):
    relative = path.relative_to(ROOT)
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("# ") or not lines[0][2:].strip():
        raise ValueError(f"{relative}:1: expected a category title")

    feeds = []
    table = None
    for number, raw_line in enumerate(lines[1:], start=2):
        line = raw_line.strip()
        location = f"{relative}:{number}"
        if not line.startswith("|"):
            if table in {"separator", "first row"}:
                raise ValueError(f"{location}: expected a table {table}")
            if table == "rows" and line:
                raise ValueError(f"{location}: expected a feed row or a blank line after the table")
            table = None
            continue

        cells = table_cells(line)
        if table is None:
            if cells != HEADER:
                raise ValueError(f"{location}: expected the catalog table header")
            table = "separator"
            continue
        if table == "separator":
            if len(cells) != len(HEADER) or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                raise ValueError(f"{location}: invalid table separator")
            table = "first row"
            continue
        if len(cells) != len(HEADER) or not all(cells):
            raise ValueError(f"{location}: expected six nonempty feed columns")
        name, website, url, feed_format, language, _description = cells
        if feed_format not in FORMATS or not re.fullmatch(r"[A-Za-z]{1,8}(?:-[A-Za-z0-9]{1,8})*", language):
            raise ValueError(f"{location}: expected RSS, Atom, or RDF and a language tag")
        website, _ = read_link(website, location)
        url, key = read_link(url, location)
        if key in seen_urls:
            raise ValueError(f"{location}: duplicate feed URL {url!r}, first listed at {seen_urls[key]}")
        seen_urls[key] = location
        feeds.append(Feed(name, website, url))
        table = "rows"

    if table in {"separator", "first row"}:
        raise ValueError(f"{relative}:{len(lines)}: incomplete feed table")
    if not feeds:
        raise ValueError(f"{relative}: expected at least one feed")
    return lines[0][2:].strip(), sorted(feeds, key=lambda feed: (feed.name.casefold(), feed.url))


def render_opml(title, groups):
    root = ET.Element("opml", version="2.0")
    ET.SubElement(ET.SubElement(root, "head"), "title").text = title
    body = ET.SubElement(root, "body")
    for folder, feeds in groups:
        parent = ET.SubElement(body, "outline", text=folder) if folder else body
        for feed in feeds:
            ET.SubElement(parent, "outline", type="rss", text=feed.name, title=feed.name,
                          xmlUrl=feed.url, htmlUrl=feed.website)
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"


def build_exports():
    seen_urls = {}
    exports = {}
    groups = []
    for directory in sorted(path for path in (ROOT / "feeds").iterdir() if path.is_dir()):
        slug = directory.name
        if slug == "all" or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError(f"{directory.relative_to(ROOT)}: invalid or reserved category slug")
        title, feeds = read_category(directory / "README.md", seen_urls)
        if any(title.casefold() == folder.casefold() for folder, _ in groups):
            raise ValueError(f"{directory.relative_to(ROOT)}/README.md:1: duplicate category title {title!r}")
        groups.append((title, feeds))
        exports[f"{slug}.opml"] = render_opml(f"Curated RSS Feeds — {title}", [(None, feeds)])
    if not groups:
        raise ValueError("feeds/: expected at least one category")
    exports["all.opml"] = render_opml("Curated RSS Feeds", groups)
    return exports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check committed exports without writing files")
    args = parser.parse_args()
    try:
        exports = build_exports()
        output = ROOT / "opml"
        existing = {path.name for path in output.glob("*.opml")}
        orphaned = existing - exports.keys()
        if orphaned:
            raise ValueError("remove orphaned exports: " + ", ".join(f"opml/{name}" for name in sorted(orphaned)))
        if args.check:
            differences = [f"opml/{name}" for name, data in exports.items()
                           if name not in existing or (output / name).read_bytes() != data]
            if differences:
                raise ValueError("missing or stale exports: " + ", ".join(differences)
                                 + " (run python3 scripts/build_opml.py)")
        else:
            output.mkdir(exist_ok=True)
            for name, data in exports.items():
                path = output / name
                if name not in existing or path.read_bytes() != data:
                    path.write_bytes(data)
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"{'Checked' if args.check else 'Generated'} {len(exports)} OPML files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
