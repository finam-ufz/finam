#!/bin/bash
echo Profiling...

mkdir -p prof

for filename in benchmarks/profiling/*.py; do
  fn=$(basename -- "$filename")
  fn="${fn%.*}"
  if [[ "$fn" == profile_* ]] ;
  then
    echo "$fn"
    python benchmarks/profiling/"$fn".py prof/"$fn".pstats
    gprof2dot --colour-nodes-by-selftime -f pstats prof/"$fn".pstats > prof/"$fn".dot
    dot -Tsvg -o prof/"$fn".svg prof/"$fn".dot
    dot -Tpng -o prof/"$fn".png prof/"$fn".dot
  fi
done

python benchmarks/pstats_to_csv.py
