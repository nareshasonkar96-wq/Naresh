#!/usr/bin/env bash
set -euo pipefail
# One-command run (generates 5 variants + zip) using the master in this folder.
IN="majorfile_master.xml"
OUT="./out"
PREFIX="majorfile_till18sep_var"
SEED=565656
CUTOFF="2025-09-18 23:59:59"
JMIN=3600    # +1h
JMAX=7200    # +2h

mkdir -p "$OUT"
python3 generate_variants.py --input "$IN" --outdir "$OUT" --num-variants 5 \
  --prefix "$PREFIX" --seed $SEED --cutoff "$CUTOFF" --jitter-min $JMIN --jitter-max $JMAX --zip-pack

echo "Done. See $OUT"
