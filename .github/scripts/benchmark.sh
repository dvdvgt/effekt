set -e
benchmarks=(
#   "are_we_fast_yet/bounce 7283"
#   "are_we_fast_yet/list_tail 42"
#   "are_we_fast_yet/mandelbrot 171"
#   "are_we_fast_yet/nbody 131072"
#   "are_we_fast_yet/permute 8"
#   "are_we_fast_yet/queens 21"
#   "are_we_fast_yet/sieve 1048576"
#   "are_we_fast_yet/storage 512"
#   "are_we_fast_yet/towers 21"
#  "duality_of_compilation/erase_unused 3642"
#  "duality_of_compilation/factorial_accumulator 8388608"
#  "duality_of_compilation/fibonacci_recursive 31"
#  "duality_of_compilation/iterate_increment 8388608"
#  "duality_of_compilation/lookup_tree 1024"
#  "duality_of_compilation/match_options 1024"
#  "duality_of_compilation/sum_range 1024"
  "effect_handlers_bench/countdown 16777216"
  "effect_handlers_bench/iterator 22369622"
  "effect_handlers_bench/nqueens 11"
  "effect_handlers_bench/parsing_dollars 7283"
  "effect_handlers_bench/product_early 32768"
  "effect_handlers_bench/resume_nontail 1366"
  "effect_handlers_bench/tree_explore 14"
  "effect_handlers_bench/triples 256"
)
out_dir="results"
backends=(
  "js"
)
feature="$FEATURE_SHA"
baseline="$BASELINE_SHA"

for label in baseline feature; do
  commit=${!label}
  git checkout "$commit"

  sbt effektJVM/assembleBinary
  chmod +x bin/effekt
  mv bin/effekt "bin/effekt_$label"
done

mkdir -p baseline feature "$out_dir"

for target in feature baseline; do
  commit=${!target}
  git checkout "$commit" > /dev/null

  for backend in "${backends[@]}"; do
    for benchmark in "${benchmarks[@]}"; do
      path=${benchmark% *}
      arg=${benchmark##* }
      filename=${path##*/}

      echo "Compiling $filename.effekt on $target using backend $backend ..."

      "./bin/effekt_$target" \
        --backend "$backend" \
        --build "examples/benchmarks/$path.effekt" \
        --out "./$target"
    done
  done
done

for benchmark in "${benchmarks[@]}"; do
  path=${benchmark% *}
  arg=${benchmark##* }
  filename=${path##*/}
    hyperfine \
      --warmup 1 \
      --show-output \
      --export-markdown "$out_dir/$filename.md" \
      --export-csv "$out_dir/$filename.csv" \
      --export-json "$out_dir/$filename.json" \
      --time-unit millisecond \
      -m 10 \
      "./baseline/$filename $arg" \
      "./feature/$filename $arg"
done | tee "./$out_dir/benchmark.log"
