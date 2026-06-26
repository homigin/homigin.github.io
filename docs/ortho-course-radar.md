# Ortho Course Radar Maintenance

The site is a static Hugo page served at `/ortho-course-radar/`.

## Files

- `static/ortho-course-radar/index.html` is the browser UI.
- `static/ortho-course-radar/events.js` is the generated event data.
- `static/ortho-course-radar/announcements.js` is the generated society announcement data.
- `static/ortho-course-radar/webinars.js` is the generated webinar data.
- `static/ortho-course-radar/last-run.json` is the latest scraper report.
- `scripts/update_ortho_course_radar.py` fetches public society pages and regenerates data.
- `.github/workflows/update-ortho-course-radar.yml` runs the scraper weekly and commits changes.
- `.github/workflows/deploy.yml` builds Hugo and publishes to GitHub Pages after commits to `main`.

## Local Update

```bash
python -m pip install -r requirements-ortho-radar.txt
python scripts/update_ortho_course_radar.py
hugo --minify
```

Commit `events.js`, `announcements.js`, `webinars.js`, and `last-run.json` if the data changed.

## Add Or Fix A Source

Edit `SOURCES`, `ANNOUNCEMENT_SOURCES`, `from_aahks_search()`, or the webinar helpers in `scripts/update_ortho_course_radar.py`.

- Use `wp="https://example.org"` for WordPress sites with `wp-json`.
- Use `urls=(...)` for normal HTML pages.
- Use `verify=False` only for known broken TLS certificates.
- Keep source pages public; do not scrape behind login.

The scraper is deliberately heuristic: it reads links and tables, keeps rows matching orthopaedic/course keywords, extracts dates, deduplicates by URL, then writes static JSON-like JavaScript.

- `bone.org.tw/education/` pagination is followed automatically, capped at a few pages.
- `mode: "lab"` is reserved for hands-on/cadaver/simulation/model/animal/patient/procedure lab wording, not every workshop.

## Known Limits

- JS-rendered pages may need a site-specific parser.
- AO uses a filtered search fallback because the site blocks simple server fetches.
- AAHKS uses the public WordPress search API as a lightweight event/news source.
- ESSKA currently returns a Cloudflare challenge to simple server fetches.
- TWSS/TASM can timeout from GitHub Actions or local networks.
- GitHub Actions is the "backend"; there is no running server.
