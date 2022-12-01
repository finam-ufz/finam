#!/bin/bash
echo Profiling...

mkdir -p prof

for filename in benchmarks/profiling/*.py; do
  fn=$(basename -- "$filename")
  fn="${fn%.*}"
  echo "$fn"
  python -m cProfile -o prof/"$fn".pstats benchmarks/profiling/"$fn".py
  gprof2dot --colour-nodes-by-selftime -f pstats prof/"$fn".pstats > prof/"$fn".dot
  dot -Tsvg -o prof/"$fn".svg prof/"$fn".dot
  dot -Tpng -o prof/"$fn".png prof/"$fn".dot
done

python benchmarks/pstats_to_csv.py
