#!/usr/bin/env python3
"""Roll the CHANGELOG.md [Unreleased] section over into a new tagged version section.

Usage: prepare_release.py <version>

Expects CHANGELOG.md to contain a "## [Unreleased]" heading followed directly
by a flat bullet list (no filler prose), and ends with a block of
"[label]: url" reference links including a "[Unreleased]: .../compare/..." line.
"""
import re
import sys
from datetime import timezone, datetime

REPO = "Nasdaq/nasdaq-protocols"
CHANGELOG = "CHANGELOG.md"


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: prepare_release.py <version>")
    version = sys.argv[1]

    with open(CHANGELOG, encoding="utf-8") as fh:
        lines = fh.read().splitlines()

    try:
        unreleased_idx = next(i for i, l in enumerate(lines) if l.strip() == "## [Unreleased]")
    except StopIteration:
        sys.exit("Could not find '## [Unreleased]' heading in CHANGELOG.md")

    next_heading_idx = next(
        (i for i in range(unreleased_idx + 1, len(lines)) if lines[i].startswith("## [")),
        len(lines),
    )

    section = lines[unreleased_idx + 1:next_heading_idx]
    # Keep bullet lines and their wrapped continuation lines; drop only blank padding.
    bullets = [l for l in section if l.strip() != ""]
    if not bullets:
        sys.exit("No entries found under [Unreleased]; nothing to release.")

    today = datetime.now(timezone.utc).date().isoformat()
    new_block = (
        ["## [Unreleased]", "", "No changes yet.", "", f"## [{version}] - {today}", ""]
        + bullets
        + [""]
    )
    lines[unreleased_idx:next_heading_idx] = new_block

    text = "\n".join(lines) + "\n"

    # Update the trailing reference-link block.
    text = re.sub(
        r"^\[Unreleased\]: .*/compare/.*\.\.\.main$",
        f"[Unreleased]: https://github.com/{REPO}/compare/{version}...main",
        text,
        flags=re.MULTILINE,
    )
    new_link = f"[{version}]: https://github.com/{REPO}/releases/tag/{version}"
    text = re.sub(
        r"^(\[Unreleased\]: .*)$",
        r"\1\n" + new_link,
        text,
        count=1,
        flags=re.MULTILINE,
    )

    with open(CHANGELOG, "w", encoding="utf-8") as fh:
        fh.write(text)

    print(f"CHANGELOG.md rolled over to {version} ({today}).")


if __name__ == "__main__":
    main()
