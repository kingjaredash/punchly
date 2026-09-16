#!/usr/bin/env python3
"""Cut a new version of Punchly.

The version lives in four places — the header chip, the service worker cache,
the in-app What's new list and CHANGELOG.md — and a deploy where they disagree
is the one failure the version chip exists to catch. So nothing here is edited
by hand: one command writes all four from the same notes, commits and tags.

    ./release.py "Colour the day strip by application" "Fix the week total on Mondays"
    ./release.py --push "Add a What's new screen"

--push sends the commit and the tag to GitHub, which is what deploys it.
--dry-run prints what would change and touches nothing.
"""

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
SW = ROOT / "sw.js"
CHANGELOG = ROOT / "CHANGELOG.md"


def fail(msg):
    print("release: " + msg, file=sys.stderr)
    sys.exit(1)


def git(*args, capture=True):
    r = subprocess.run(["git", "-C", str(ROOT)] + list(args),
                       capture_output=capture, text=True)
    if r.returncode != 0:
        fail("git " + " ".join(args) + " failed\n" + (r.stderr or "").strip())
    return (r.stdout or "").strip()


def read_versions():
    index, sw = INDEX.read_text(), SW.read_text()
    m = re.search(r'var BUILD = "(v\d+)"', index)
    if not m:
        fail("no BUILD constant in index.html")
    c = re.search(r'const CACHE = "punchly-(v\d+)"', sw)
    if not c:
        fail("no CACHE constant in sw.js")
    if m.group(1) != c.group(1):
        fail("BUILD is %s but CACHE is %s — fix the drift before releasing"
             % (m.group(1), c.group(1)))
    return m.group(1)


def bump(current):
    return "v" + str(int(current[1:]) + 1)


def write_index(version, date, notes, dry):
    s = INDEX.read_text()
    s2 = re.sub(r'var BUILD = "v\d+"', 'var BUILD = "%s"' % version, s, count=1)
    s2 = re.sub(r'var BUILT = "[\d-]+"', 'var BUILT = "%s"' % date, s2, count=1)

    entry = ('  {v:%s, d:%s, n:[\n' % (json.dumps(version), json.dumps(date))
             + ",\n".join("    " + json.dumps(n) for n in notes)
             + "\n  ]},\n")
    anchor = "var RELEASES = [\n"
    if anchor not in s2:
        fail("no RELEASES array in index.html")
    s2 = s2.replace(anchor, anchor + entry, 1)

    if not dry:
        INDEX.write_text(s2)
    return s != s2


def write_sw(version, dry):
    s = SW.read_text()
    s2 = re.sub(r'const CACHE = "punchly-v\d+"',
                'const CACHE = "punchly-%s"' % version, s, count=1)
    if not dry:
        SW.write_text(s2)
    return s != s2


def write_changelog(version, date, notes, dry):
    head = ("# Changelog\n\nEvery deployed version of Punchly, newest first. "
            "Written by `release.py`;\nthe same notes appear in the app under "
            "What's new.\n")
    body = CHANGELOG.read_text() if CHANGELOG.exists() else head
    if not body.startswith("# Changelog"):
        fail("CHANGELOG.md does not start with its heading")

    entry = "\n## %s — %s\n\n" % (version, date) + "".join("- %s\n" % n for n in notes)
    lines = body.split("\n")
    cut = next((i for i, l in enumerate(lines) if l.startswith("## ")), len(lines))
    out = "\n".join(lines[:cut]).rstrip("\n") + "\n" + entry + "\n" + "\n".join(lines[cut:]).lstrip("\n")
    if not dry:
        CHANGELOG.write_text(out.rstrip("\n") + "\n")
    return True


def main():
    ap = argparse.ArgumentParser(add_help=True, description="Cut a new version of Punchly.")
    ap.add_argument("notes", nargs="+", help="one changelog line per argument")
    ap.add_argument("--push", action="store_true", help="push the commit and tag to GitHub")
    ap.add_argument("--dry-run", action="store_true", help="show what would change")
    args = ap.parse_args()

    notes = [n.strip() for n in args.notes if n.strip()]
    if not notes:
        fail("a release needs at least one note")

    current = read_versions()
    version = bump(current)
    date = datetime.date.today().isoformat()

    if git("tag", "-l", version):
        fail("tag %s already exists" % version)

    print("%s → %s  (%s)" % (current, version, date))
    for n in notes:
        print("  - " + n)

    write_index(version, date, notes, args.dry_run)
    write_sw(version, args.dry_run)
    write_changelog(version, date, notes, args.dry_run)

    if args.dry_run:
        print("\ndry run — nothing written, nothing committed")
        return

    if read_versions() != version:
        fail("version did not land in both files — nothing committed")

    git("add", "-A")
    if not git("diff", "--cached", "--name-only"):
        fail("nothing staged — did the edits land?")

    message = ("Release %s\n\n" % version + "".join("- %s\n" % n for n in notes)
               + "\nCo-Authored-By: Claude Opus 5 <noreply@anthropic.com>\n")
    git("commit", "-m", message)
    git("tag", "-a", version, "-m", "Punchly %s" % version)
    print("\ncommitted and tagged %s" % version)

    if args.push:
        git("push", capture=False)
        git("push", "origin", version, capture=False)
        print("pushed — GitHub Pages redeploys on its own")
    else:
        print("next:  git push && git push origin %s" % version)


if __name__ == "__main__":
    main()
