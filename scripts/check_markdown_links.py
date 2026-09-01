#!/usr/bin/env python3
"""Check repository Markdown files for broken relative links."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
ROOT_MARKDOWN_FILES = (
    "README.md",
    "CONTRIBUTING.md",
    "ROADMAP.md",
    "CHANGELOG.md",
)
COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
FENCE_PATTERN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
REFERENCE_PATTERN = re.compile(
    r"^[ \t]{0,3}\[(?!\^)[^\]\n]+\]:[ \t]*(?:<([^>]+)>|(\S+))"
)


def markdown_files(root: Path) -> list[Path]:
    """Return the repository Markdown files covered by the check."""
    paths = [root / name for name in ROOT_MARKDOWN_FILES if (root / name).is_file()]
    docs = root / "docs"
    if docs.is_dir():
        paths.extend(path for path in docs.rglob("*.md") if path.is_file())
    return sorted(paths, key=lambda path: path.relative_to(root).as_posix())


def _is_escaped(text: str, index: int) -> bool:
    backslashes = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        backslashes += 1
        index -= 1
    return backslashes % 2 == 1


def _mask_comments(text: str) -> str:
    return COMMENT_PATTERN.sub(
        lambda match: "".join(
            "\n" if character == "\n" else " " for character in match.group()
        ),
        text,
    )


def _mask_inline_code(line: str) -> str:
    visible = list(line)
    index = 0
    while index < len(line):
        if line[index] != "`" or _is_escaped(line, index):
            index += 1
            continue
        end = index
        while end < len(line) and line[end] == "`":
            end += 1
        delimiter = line[index:end]
        closing = line.find(delimiter, end)
        if closing == -1:
            index = end
            continue
        visible[index : closing + len(delimiter)] = " " * (
            closing + len(delimiter) - index
        )
        index = closing + len(delimiter)
    return "".join(visible)


def _visible_lines(text: str) -> list[str]:
    """Hide top-level fenced blocks, comments, and same-line code spans."""
    lines: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    for line in _mask_comments(text).splitlines():
        fence = FENCE_PATTERN.match(line)
        if fence_character is not None:
            if (
                fence is not None
                and fence.group(1)[0] == fence_character
                and len(fence.group(1)) >= fence_length
                and not fence.group(2).strip()
            ):
                fence_character = None
                fence_length = 0
            lines.append("")
            continue
        if fence is not None:
            marker, info = fence.groups()
            if marker[0] == "~" or "`" not in info:
                fence_character = marker[0]
                fence_length = len(marker)
                lines.append("")
                continue
        lines.append(_mask_inline_code(line))
    return lines


def _destination(line: str, start: int) -> str | None:
    while start < len(line) and line[start].isspace():
        start += 1
    if start >= len(line):
        return None
    if line[start] == "<":
        closing = line.find(">", start + 1)
        if closing == -1 or ")" not in line[closing + 1 :]:
            return None
        return line[start + 1 : closing]

    target: list[str] = []
    depth = 1
    escaped = False
    collecting = True
    for character in line[start:]:
        if escaped:
            if collecting:
                target.append(character)
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == "(":
            depth += 1
            if collecting:
                target.append(character)
        elif character == ")":
            depth -= 1
            if depth == 0:
                return "".join(target) or None
            if collecting:
                target.append(character)
        elif character.isspace() and depth == 1:
            collecting = False
        elif collecting:
            target.append(character)
    return None


def _inline_targets(line: str) -> list[str]:
    targets: list[str] = []
    opening = 0
    while opening < len(line):
        opening = line.find("[", opening)
        if opening == -1:
            break
        if _is_escaped(line, opening):
            opening += 1
            continue

        depth = 1
        closing = opening + 1
        while closing < len(line) and depth:
            if line[closing] == "\\":
                closing += 2
                continue
            if line[closing] == "[":
                depth += 1
            elif line[closing] == "]":
                depth -= 1
            closing += 1
        if depth == 0 and line[closing : closing + 1] == "(":
            target = _destination(line, closing + 1)
            if target is not None:
                targets.append(target)
        opening += 1
    return targets


def _link_targets(text: str) -> list[str]:
    targets: list[str] = []
    for line in _visible_lines(text):
        definition = REFERENCE_PATTERN.match(line)
        if definition is not None:
            targets.append(definition.group(1) or definition.group(2))

        targets.extend(_inline_targets(line))
    return targets


def _is_broken(root: Path, source: Path, target: str) -> bool:
    if target.startswith("#") or target.startswith("//"):
        return False
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return False

    resolved_root = root.resolve()
    resolved_target = (source.parent / unquote(parsed.path)).resolve()
    try:
        resolved_target.relative_to(resolved_root)
    except ValueError:
        return True
    return not resolved_target.exists()


def find_broken_links(root: Path = ROOT) -> list[str]:
    """Return deterministic ``source: target`` entries for broken local links."""
    broken: set[str] = set()
    for source in markdown_files(root):
        source_name = source.relative_to(root).as_posix()
        for target in _link_targets(source.read_text(encoding="utf-8")):
            if _is_broken(root, source, target):
                broken.add(f"{source_name}: {target}")
    return sorted(broken)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="repository root to check (defaults to this checkout)",
    )
    args = parser.parse_args(argv)
    try:
        broken = find_broken_links(args.root)
    except OSError as exc:
        print(f"Markdown link check failed: {exc}", file=sys.stderr)
        return 1
    if broken:
        for entry in broken:
            print(f"broken Markdown link: {entry}", file=sys.stderr)
        return 1
    print(f"Markdown link check passed for {len(markdown_files(args.root))} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
