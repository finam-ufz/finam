echo Profiling...

mkdir -p prof

python -m cProfile -o prof/simple_run.pstats benchmarks/profiling/simple_run.py
gprof2dot --colour-nodes-by-selftime -f pstats prof/simple_run.pstats > prof/simple_run.dot
dot -Tsvg -o prof/simple_run.svg prof/simple_run.dot
dot -Tpng -o prof/simple_run.png prof/simple_run.dot

python benchmarks/pstats_to_csv.py
