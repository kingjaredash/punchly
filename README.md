# Punchly

An installable web app for logging the time you spend in **TempTrak** and
**TheWorxHub**. Punch in when you start, punch out when you stop, and get the
hours back as a pasteable summary, a CSV, or a week at a glance.

Runs in your phone's browser from a home-screen icon, and keeps working with no
signal — which matters, because a mechanical room is exactly where the timer
needs to start and exactly where the bars run out.

Colour carries the meaning throughout: **ember is TempTrak, teal is
TheWorxHub**, in every chip, every total and every block on the day strip. The
rest of the interface stays black on manila, so the only colour on screen is
information.

## Deploying to GitHub Pages

The `gh` CLI isn't installed on this machine, so the repo has to be created
through the web UI. Two steps are yours, one is a paste.

1. Create an empty repo at <https://github.com/new>. Name it `punchly`. No
   README, no .gitignore, no licence: this folder already has a commit.

2. Push. SSH is already authorised for this account, so no token is needed:

   ```sh
   cd ~/punchly
   git remote add origin git@github.com:kingjaredash/punchly.git
   git push -u origin main
   ```

3. In the repo: **Settings → Pages → Source: Deploy from a branch**, branch
   `main`, folder `/ (root)`. Save. The first build takes a minute or two.

Your app then lives at `https://kingjaredash.github.io/punchly/`.

## Putting an icon on your phone

Open the Pages URL on the phone, then:

- **iPhone (Safari):** Share → Add to Home Screen → Add.
- **Android (Chrome):** ⋮ → Add to Home screen.

You get a home-screen icon that opens the page in your normal browser, with the
address bar, tabs, back button and share sheet where you expect them. The
manifest sets `"display": "browser"` and the page deliberately omits
`apple-mobile-web-app-capable`, which is what keeps it a browser page rather
than a standalone app. To switch to full-screen app behaviour instead, set
`"display": "standalone"` in `manifest.webmanifest`, add
`<meta name="apple-mobile-web-app-capable" content="yes">` to `index.html`,
bump `CACHE` in `sw.js`, and re-add the icon on the phone.

## Punching in and out

**One clock runs at a time.** Punching into TheWorxHub while TempTrak is
running closes the TempTrak entry at that instant and opens a new one — the
**Switch** button on the running card is exactly that, and it carries the
customer and ticket across, since switching applications usually means the same
job seen from the other side.

Details can wait. Punch in with two taps and nothing else; when you punch out
the app opens that entry so you can write down what you actually did while it's
still fresh. Everything is editable afterwards, including the start and end
times — a timer left running overnight says so on the card, and you fix the end
time rather than throwing the entry away.

An entry whose end time is earlier than its start is read as work that ran past
midnight, and counts as the hours it really took. It's reported on the day it
started.

The **Today** tab draws the day as a strip on a clock scale, so an afternoon
you forgot to log looks like a gap rather than arithmetic you have to do.

## Getting the hours out

The **Report** tab takes a range — today, this week, last week, this month, or
two dates you pick — and gives you:

- the total, split TempTrak against TheWorxHub;
- breakdowns by day, by customer or site, and by task type;
- **Copy summary**, which puts a formatted plain-text rundown on the clipboard,
  ready to paste into a timesheet or an email;
- **Download CSV**, with the columns
  `Date, Start, End, Hours, Application, Customer, Ticket, Task, Notes`.

### Rounding

**Round each entry to** applies to everything the Report shows and exports:
exact minutes, tenths of an hour (6 min), or quarter hours (15 min). Rounding
is applied per entry to the nearest increment, but a non-zero entry never
rounds down to nothing — a four-minute call still bills a quarter hour when
you're on quarters. The raw start and end times are kept whatever you pick, so
changing the setting re-reports the same entries rather than editing them.

**Week starts** decides what "this week" means, and where the header's week
total resets. Sunday by default.

## URLs the app answers to

Every screen is reachable by URL, which is what makes Siri and Apple Shortcuts
useful. Append to the Pages URL:

| URL            | Does                                      |
| -------------- | ----------------------------------------- |
| `?punch=tt`    | punches in on TempTrak, right now         |
| `?punch=wx`    | punches in on TheWorxHub                  |
| `?stop`        | punches out                               |
| `?go=new`      | the form for logging time by hand         |
| `?go=log`      | the whole log                             |
| `?go=report`   | totals and export                         |

### Apple Shortcuts

Four worth building, each one action. In the Shortcuts app: **+ → Add Action →
Web → Open URLs**, then **⌄ → Rename / Choose Icon**, and **Add to Home Screen**
from the share menu.

- **Start TempTrak** — `Open URLs` with `https://kingjaredash.github.io/punchly/?punch=tt`
- **Start WorxHub** — the same with `?punch=wx`
- **Punch out** — the same with `?stop`
- **Log time** — `?go=new`, for the drive home when you forgot to start it

Rename each one carefully: the name *is* the Siri phrase. "Hey Siri, start
TempTrak" from the truck is the whole point. On an iPhone 15 Pro or newer, any
of them can also go on the Action Button.

## Your data

Entries live in the browser's `localStorage` on each device, and the app works
fully offline with no account at all.

**Report → Save a backup file** exports JSON; **Restore from a backup** merges
one back in, entry by entry, keeping whichever copy was edited later. Keep a
backup in iCloud Drive regardless of anything below: Safari deletes a site's
storage after seven days without a visit.

### Syncing two devices

The **Sync** tab connects the app to a free Supabase project so the phone and
the computer share one log. Setup is once, on the first device:

1. Create a free project at <https://supabase.com> (no card).
2. SQL editor → paste `supabase-setup.sql` → Run.
3. Project Settings → API → copy the **Project URL** and the **anon public**
   key into the Sync tab → Connect.

**Every other device joins rather than repeats that.** Typing the URL and key
again mints a fresh, empty log — the connection works but no entries appear.
Instead, on a device that already syncs, open **Sync** and either scan the
pairing code with the other phone's camera or press **Copy pairing link** and
paste it into the other browser's address bar or its Join field. The pairing
data carries the ledger id, which is what actually identifies your log.

The Sync tab shows the first characters of that id; every device sharing your
entries shows the same one.

**How it behaves.** Each entry carries its own `updatedAt`, and the newer edit
wins per entry — so two devices editing different entries never conflict, and
two editing the same one settle on the later change. Deletes propagate as
tombstones. Offline edits queue and go up on the next sync, and a device that
has been dark for a week cannot overwrite newer work when it returns. Syncing
happens on load, when the tab regains focus, when the network returns, and a
second or so after any edit. A running timer syncs too, so a clock started on
the phone shows on the laptop.

**How it's secured.** The `punchly_entries` table has RLS on with no policies
and no grants to `anon`, so the public key alone reaches nothing — no reads, no
dumps. Everything goes through two `security definer` functions that require
the ledger id, a 128-bit random string generated on your device that only
travels between your devices. Treat the pairing QR like a password. This is
unguessable-identifier security rather than per-user accounts, which suits a
personal time log; it is not what you'd use for anything regulated.

## Updating it

Edit `index.html`, then bump **both** `BUILD` in `index.html` and `CACHE` in
`sw.js` — keep them equal. `BUILD` shows in the header, so you can tell at a
glance which version a device is running; tapping it asks the server what the
current build is, and if the device is behind it clears the caches and reloads.
`CACHE` (`punchly-v1` → `v2`, and so on) is what makes installed phones fetch
the new version instead of serving the cached one. Commit and push; Pages
redeploys on its own.

## Layout

```
index.html                 the whole app: markup, styles, logic
manifest.webmanifest       name, icons, display mode
sw.js                      offline cache — bump CACHE on every deploy
supabase-setup.sql         table and RPCs for the optional sync backend
icons/                     generated PNGs (the punch-card mark)
vendor/qrcode.js           QR encoding, for the pairing code
```

The QR library is vendored rather than loaded from a CDN so the app works with
no network at all.
