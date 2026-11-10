# danhenriquex.github.io

Portfolio site that **builds itself from my GitHub repositories**. No hand-written project pages.

## How it works

1. `scripts/build.py` reads every public repo (description, topics, languages, file tree,
   `package.json` / `requirements.txt` / `pyproject.toml` / `docker-compose.yml` / Python imports, and the README).
2. It detects the tech stack, picks a category (AI & LLMs, Machine Learning, Data Engineering, Web, Mobile, …),
   extracts a summary and cover image from the README, and writes `_site/` (static HTML/CSS/JS + `data/projects.json`).
   Repos **without a README** get a summary generated from their stack.
3. `.github/workflows/deploy.yml` runs the build and deploys to GitHub Pages **on every push, daily at 06:00 UTC,
   and on demand** (Actions → *Build and deploy portfolio* → *Run workflow*).

## Customising

Edit `portfolio.config.json`:

| key | what it does |
| --- | --- |
| `featured` | repos shown in the Featured section, in this order |
| `exclude` | repos never shown |
| `headline`, `tagline`, `links` | hero text, and the header/hero buttons (GitHub, LinkedIn, CV…) |
| `include_forks`, `include_archived` | include forks / archived repos |

From GitHub itself (no code change): add the topic **`featured`** to feature a repo, **`portfolio-hide`** to hide it.
The repo's *About → Description* becomes the card summary and *Website* becomes the "Live demo" button.

## Local preview

```bash
GITHUB_TOKEN=$(gh auth token) python3 scripts/build.py
python3 -m http.server -d _site 8000   # http://localhost:8000
```

## READMEs for repos that don't have one

```bash
GITHUB_TOKEN=$(gh auth token) python3 scripts/build.py --readme-drafts   # writes readme-drafts/<repo>/README.md
# review / edit the drafts, then:
scripts/push_readmes.sh              # all drafts
scripts/push_readmes.sh Projeto-Apa  # or just some
```
