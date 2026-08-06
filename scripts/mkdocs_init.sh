#!/usr/bin/env bash
# Scaffold an MkDocs site for a folder that doesn't have one yet:
#   1. <folder>/docs/  — symlinks to that folder's markdown-bearing top-level entries,
#      mirroring the pattern engineering_fundamentals already uses (so the real files
#      stay where they are; docs/ is just a curated view mkdocs reads from).
#   2. <folder>/mkdocs.yml — material theme, docs_dir: docs, no explicit nav (MkDocs
#      auto-generates navigation from the directory tree — fine as a default; hand-edit
#      the nav later if a curated order is wanted, same as the three existing sites did).
#
# docs/ and mkdocs.yml are both fully reproducible from the folder's own content, so this
# script gitignores them rather than leaving them to be committed — running `make init` (or
# `make docs`) again regenerates them identically, nothing to keep in sync by hand or commit
# twice (once at the real path, once again as a symlink/derived config). If a folder's site
# grows into something worth hand-curating (a real nav, extra pages) the same way
# engineering_fundamentals/k8s_explorer/genai_lab did, just remove it from that folder's
# .gitignore and commit docs/ + mkdocs.yml normally from that point on.
#
# Usage: scripts/mkdocs_init.sh <folder>
set -euo pipefail

FOLDER="${1:?Usage: scripts/mkdocs_init.sh <folder>}"

if [ ! -d "$FOLDER" ]; then
	echo "No such folder: $FOLDER" >&2
	exit 1
fi

if [ -f "$FOLDER/mkdocs.yml" ]; then
	echo "$FOLDER/mkdocs.yml already exists — nothing to do."
	exit 0
fi

# Names to never treat as documentation content, whether files or directories.
EXCLUDE_NAMES=(docs site .git .venv venv node_modules __pycache__ .pytest_cache .mypy_cache dist build)

is_excluded() {
	local name="$1"
	for x in "${EXCLUDE_NAMES[@]}"; do
		[ "$name" = "$x" ] && return 0
	done
	case "$name" in
		.*) return 0 ;; # any dotfile/dotdir
	esac
	return 1
}

dir_has_markdown() {
	# True if $1 contains at least one .md file anywhere below it, without descending
	# into excluded subdirectories (keeps this fast even next to a huge .venv/).
	local prune_expr=()
	for x in "${EXCLUDE_NAMES[@]}"; do
		prune_expr+=(-name "$x" -o)
	done
	# drop the trailing -o
	unset 'prune_expr[${#prune_expr[@]}-1]'
	find "$1" \( "${prune_expr[@]}" \) -prune -o -iname '*.md' -print -quit | grep -q .
}

mkdir -p "$FOLDER/docs"

linked_any=false
for entry in "$FOLDER"/*; do
	name="$(basename "$entry")"
	is_excluded "$name" && continue

	if [ -f "$entry" ] && [[ "$name" == *.md ]]; then
		ln -sf "../$name" "$FOLDER/docs/$name"
		linked_any=true
	elif [ -d "$entry" ] && dir_has_markdown "$entry"; then
		ln -sf "../$name" "$FOLDER/docs/$name"
		linked_any=true
	fi
done

if [ "$linked_any" = false ]; then
	echo "No markdown found under $FOLDER (besides excluded dirs) — nothing to link." >&2
	rmdir "$FOLDER/docs" 2>/dev/null || true
	exit 1
fi

SITE_NAME="$(basename "$FOLDER")"

# MkDocs needs an index.md/README.md at the docs root to have a homepage at all — without
# one, '/' 404s even though every other page serves fine. Folders like a flat directory of
# numbered notes (no README.md of their own) hit this. Generate a simple auto-index only
# when nothing already serves as one. The file list is captured *before* index.md is
# created, since `> docs/index.md` would otherwise truncate-create it first, making it
# match its own `*.md` glob and self-list.
if ! ls "$FOLDER/docs" | grep -qiE '^(index|readme)\.md$'; then
	existing_pages=("$FOLDER"/docs/*.md)
	{
		echo "# ${SITE_NAME}"
		echo
		echo "Auto-generated index — this folder has no README.md/index.md of its own."
		echo
		for f in "${existing_pages[@]}"; do
			[ -e "$f" ] || continue
			base="$(basename "$f")"
			title="$(awk 'NR==1{gsub(/^#+[ \t]*/,""); print; exit}' "$f")"
			[ -z "$title" ] && title="$base"
			echo "- [${title}](${base})"
		done
	} > "$FOLDER/docs/index.md"
fi

# docs/ and mkdocs.yml here are both fully reproducible from this folder's own content —
# docs/ is only symlinks back to files already tracked at their real path, and mkdocs.yml
# is a deterministic template `make init` regenerates identically every time. Committing
# them would mean committing the same content twice (once at its real path, once again as
# a symlink/derived config); gitignoring them instead means `make docs`/`make init` is the
# one source of truth, run on demand, nothing to keep in sync by hand. site/ (the actual
# build output) is excluded for the same reason the three hand-curated sites already do.
for pattern in docs/ mkdocs.yml site/; do
	if [ -f "$FOLDER/.gitignore" ]; then
		grep -qx "$pattern" "$FOLDER/.gitignore" || printf '%s\n' "$pattern" >> "$FOLDER/.gitignore"
	else
		printf '%s\n' "$pattern" > "$FOLDER/.gitignore"
	fi
done

cat > "$FOLDER/mkdocs.yml" <<EOF
site_name: ${SITE_NAME}
docs_dir: docs
site_dir: site

theme:
  name: material
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      toggle:
        icon: material/weather-night
        name: Switch to dark mode
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      toggle:
        icon: material/weather-sunny
        name: Switch to light mode
  features:
    - navigation.sections
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy

markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.highlight:
      anchor_linenums: true
  - toc:
      permalink: true
  - tables

# No explicit nav: MkDocs auto-generates it from docs/'s directory tree.
# Add a hand-curated 'nav:' section here later if a specific order/grouping is wanted —
# see engineering_fundamentals/mkdocs.yml, k8s_explorer/mkdocs.yml, or
# genai_lab/mkdocs.yml for worked examples of that pattern.
EOF

echo "Scaffolded $FOLDER/docs/ (symlinks) and $FOLDER/mkdocs.yml"
echo "Run: make serve FOLDER=$FOLDER"
