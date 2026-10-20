# Content types & metadata

SNAP Records stores label content as `content_items`. Each item sits in a **section** (stored as `category`), has an **audience_level** (who can see it), optional embargo timestamps, and a file on disk.

## Sections (dashboard)

| Section (`category`) | Label | Typical content |
|----------------------|-------|-----------------|
| `new_music` | New Music | Singles, albums, demos, masters, stems |
| `merch` | Merch | Tees, hoodies, drops, crew kit notes |
| `band_pages` | Band Pages | Bio, about, photos, riders, contracts |
| `news` | News | Announcements, BTS, press-facing drops |

Who sees an item is still controlled by **audience** + grants + time windows — not by the section alone. A press master lives under New Music with `audience_level = press`.

## Audience levels

| Level | Intent |
|-------|--------|
| `public` | Any registered user |
| `fan_club` | Fan club (after fan window) |
| `press` | Press/partners (after press window) |
| `crew` | Tour / production |
| `band` | Band members |
| `restricted` | Explicit grants only (+ band members can still manage) |

## Example seed items

| Title | Section | Audience |
|-------|---------|----------|
| SNAP — Midnight (single) | New Music | public |
| SNAP — Album X (press master) | New Music | press |
| SNAP logo tee | Merch | public |
| About SNAP | Band Pages | public |
| EU 2026 tour rider | Band Pages | crew |
| Tour dates announced | News | public |
| Fan club BTS drop | News | fan_club |

## Related docs

- [DATA_MODEL.md](DATA_MODEL.md)
- [ACCESS_CONTROL.md](ACCESS_CONTROL.md)
- [PAGES.md](PAGES.md)
