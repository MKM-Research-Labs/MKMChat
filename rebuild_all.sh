#!/usr/bin/env bash
# Sequentially rebuild FAISS for the given knowledge bases on a single CPU
# thread. Waits for any in-flight refaiss.py run to finish first, so total
# load stays single-threaded throughout.
#
# Usage:
#   bash rebuild_all.sh                 # defaults to: hist corp mods
#   bash rebuild_all.sh phys hist corp  # explicit list
set -u
cd /Users/newdavid/Documents/MKMChat || exit 1

# Don't start until any current rebuild has finished (keeps it 1 thread total).
while pgrep -f "refaiss.py --kb" >/dev/null 2>&1; do
  echo ">>> $(date '+%H:%M:%S') waiting for current rebuild to finish..."
  sleep 30
done

kbs=("$@")
[ ${#kbs[@]} -eq 0 ] && kbs=(hist corp mods)

for kb in "${kbs[@]}"; do
  echo ">>> $(date '+%Y-%m-%d %H:%M:%S') starting $kb"
  .venv/bin/python refaiss.py --kb "$kb" --yes --threads 1
  echo ">>> $(date '+%Y-%m-%d %H:%M:%S') finished $kb"
done
echo ">>> ALL DONE $(date '+%Y-%m-%d %H:%M:%S')"
