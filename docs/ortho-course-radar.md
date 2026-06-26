# Ortho Course Radar Maintenance

The site is a static Hugo page served at `/ortho-course-radar/`.

## Files

- `static/ortho-course-radar/index.html` is the browser UI.
- `static/ortho-course-radar/events.js` is the generated event data.
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

Commit `events.js` and `last-run.json` if the data changed.

## Add Or Fix A Source

Edit the `SOURCES` list in `scripts/update_ortho_course_radar.py`.

- Use `wp="https://example.org"` for WordPress sites with `wp-json`.
- Use `urls=(...)` for normal HTML pages.
- Use `verify=False` only for known broken TLS certificates.
- Keep source pages public; do not scrape behind login.

The scraper is deliberately heuristic: it reads links and tables, keeps rows matching orthopaedic/course keywords, extracts dates, deduplicates by URL, then writes static JSON-like JavaScript.

## Known Limits

- JS-rendered pages may need a site-specific parser.
- AO and TWSS currently need better public entry URLs.
- GitHub Actions is the "backend"; there is no running server.
