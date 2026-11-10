#!/usr/bin/env bash
# Push the README drafts in readme-drafts/<repo>/README.md to each repository.
# Review/edit the drafts first:  python3 scripts/build.py --readme-drafts
# Usage: scripts/push_readmes.sh [repo ...]   (default: every draft)
set -euo pipefail
cd "$(dirname "$0")/.."
OWNER=$(python3 -c "import json;print(json.load(open('portfolio.config.json'))['username'])")
repos=("$@")
[ ${#repos[@]} -eq 0 ] && repos=($(ls readme-drafts))
for repo in "${repos[@]}"; do
  file="readme-drafts/$repo/README.md"
  [ -f "$file" ] || { echo "skip $repo (no draft)"; continue; }
  if gh api "repos/$OWNER/$repo/readme" >/dev/null 2>&1; then
    echo "skip $repo (already has a README)"; continue
  fi
  gh api -X PUT "repos/$OWNER/$repo/contents/README.md" \
    -f message="Add README" \
    -f content="$(base64 < "$file" | tr -d '\n')" >/dev/null
  echo "pushed $repo"
done
