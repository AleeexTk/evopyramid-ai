#!/usr/bin/env bash
# Remove Windows Explorer metadata files from the working tree and staging area.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mapfile -t TRACKED_FILES < <(cd "$ROOT_DIR" && git ls-files -z -- 'Desktop.ini' 'Thumbs.db' | tr '\0' '\n')
if (( "${#TRACKED_FILES[@]}" > 0 )); then
  (cd "$ROOT_DIR" && git rm --cached --quiet -- "${TRACKED_FILES[@]}")
fi

mapfile -t REMOVED_FILES < <(find "$ROOT_DIR" -type f \( -name 'Desktop.ini' -o -name 'Thumbs.db' \) -not -path '*/.git/*')
if (( "${#REMOVED_FILES[@]}" > 0 )); then
  rm -f "${REMOVED_FILES[@]}"
fi

if (( "${#TRACKED_FILES[@]}" > 0 )); then
  printf 'Removed %d tracked Windows metadata file(s) from staging.\n' "${#TRACKED_FILES[@]}"
fi

if (( "${#REMOVED_FILES[@]}" > 0 )); then
  printf 'Deleted %d Windows metadata file(s) from the working tree.\n' "${#REMOVED_FILES[@]}"
fi

echo 'Workspace cleaned of Desktop.ini and Thumbs.db artifacts.'
