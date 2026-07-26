---
status: active
updated: 2026-07-25
---

# Homigin Website Project

This repo is the project folder for the public website. Keep website planning, copy, and implementation notes here instead of the main vault.

## Source

- Repo: `/Users/chiayuan/Github/homigin.github.io`
- Public site: `https://homigin.github.io/`
- Local preview: `http://localhost:1313/`

## Current Structure

- `content/about/index.md`: professional CV / about page
- `content/posts/`: all articles, categorized with front matter `tags`
- `content/tools/index.md`: public tools
- `content/resources/index.md`: recommended links and resources
- `config.toml`: Hugo / PaperMod site config and menu

## Current Direction

- Make the site a lightweight landing page for an orthopaedic professional.
- Keep the style close to PaperMod defaults.
- Put real content first; skip empty CV sections until there is real material.

## Next

- Review `/about/` copy in browser.
- Add avatar or OG image only when there is a good source image.
- Decide whether Medium posts should stay external links or be copied into `content/`.

## Maintenance

- Add self-built projects to `content/tools/index.md`.
- Add recommended links and tools I use to `content/resources/index.md`.
- Add new articles under `content/posts/` and classify them with `tags`; do not create topic sections.
- Keep the main menu short: articles, tags, tools, resources, radar, about.
- When moving a published article, preserve its previous URL in front matter `aliases`.
- Keep unfinished or empty notes as `draft: true` instead of publishing placeholder pages.
- Keep long series such as CSCS chapters out of the homepage with `hiddenInHomeList: true`; link them from one overview article.
- Use collapsed TOCs and compact Markdown lists for long study notes. Shared readability styles live in `assets/css/extended/content-readability.css`.

## Useful Codex Skills

- `humanizer-zh`: polish Chinese copy before publishing.
- `browser:control-in-app-browser`: check mobile and desktop layout.
- `github:yeet`: commit, push, and open a PR when the batch is ready.
- `imagegen`: make an avatar or OG image when there is a clear visual direction.
