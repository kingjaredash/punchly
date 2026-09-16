# Changelog

Every deployed version of Punchly, newest first. Written by `release.py`;
the same notes appear in the app under What's new.

## v2 — 2026-09-15

- Add a What's new screen: the version chip now opens the release history and checks whether this device is behind the published build.
- Add release.py, which writes the version into index.html, sw.js, the in-app history and CHANGELOG.md from one set of notes, then commits and tags it.

## v1 — 2026-09-15

- First release. Punch in and out of TempTrak and TheWorxHub, one clock at a time.
- Customer, ticket, task type and notes on every entry.
- Reports by day, customer and task, with rounding to tenths or quarters.
- Copy a summary, download a CSV, save a backup.
- Optional sync across devices through a Supabase project.
