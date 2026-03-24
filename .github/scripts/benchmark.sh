set -e

benchmarks=()
while IFS= read -r line || [[ -n "$line" ]]; do
 [[ "$line" =~ ^\s*# ]] && continue  # skip comments
 [[ "$line" =~ ^\s*$ ]] && continue  # skip blank lines
 benchmarks+=("$line")
done < "$CONFIG_FILE"

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
      --export-json "$out_dir/$filename.json" \
      --time-unit millisecond \
      -m 10 \
      "./baseline/$filename $arg" \
      "./feature/$filename $arg"
done | tee "./$out_dir/benchmark.log"
