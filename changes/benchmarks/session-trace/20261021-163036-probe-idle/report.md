# Session trace benchmark — 20261021-163036-probe-idle

## Setup

- Created 2026-10-21T16:30:36+02:00; 4 repetitions + 1 warm-up round(s) (excluded); variants rotate per round (A B C, B C A, …); one cold browser context per run.
- Machine: 13th Gen Intel(R) Core(TM) i7-1365U, 12 logical cores, 31.3 GB RAM, Windows-11-10.0.26200-SP0; power: GUID des Energieschemas: 381b4222-f694-41f0-9685-ff5bb260df2e  (Ausbalanciert), AC True.
- GL JS gl7-performance-optimization @ f9bd50a8b5 (dirty); worker count 1; viewport {'width': 1280, 'height': 1024}; tracing preset devtools.
- Python 3.12.2, packages {'playwright': '1.64.0', 'numpy': '2.5.3', 'matplotlib': '3.11.2'}.

| variant | bundle | format | bundle sha256 | branch build |
|---|---|---|---|---|
| MLT | `dist/maplibre-gl-dev.mjs` | mlt | `b2691453151d` | – |

| session | style | duration | frames | sha256 |
|---|---|---:|---:|---|
| session-smoke | osm-bright | 8.0 s | 360 | `31a0e49d65a0` |

CPU sampling interval (median over runs): 622 µs.

## Definitions

- **busy** = wall time in which a GL JS worker thread runs a task (union of top-level task slices and GC slices on `DedicatedWorker thread`s), summed over workers. **GC** = union of `MinorGC`/`MajorGC`/`V8.GC*` slices on those threads. **busy without GC** = busy − GC (headline metric).
- **CPU** = thread time (`tdur`) of the same slices. Phase categories and functions come from the trace's CPU samples (self time), categorised by `config/categories.toml` (nearest matching frame, leaf to root).
- Windows: **load** = map creation → first idle; **session** = camera replay; **tail** = end of replay → idle; **total** = load + session + tail.
- Ratios are against **MLT**: ratio of medians with a bootstrap 95 % CI, the geometric mean of per-round ratios, and a two-sided Mann–Whitney U p-value (normal approximation, not corrected for multiple comparisons; rough below n = 8). Lower than 1× means less worker time.

## Session `session-smoke`

### Worker busy without GC (session window)

| variant | n ok / failed | median ms | IQR | mean | ratio vs MLT | 95 % CI | geo-mean paired | MWU p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| MLT | 4 / 0 | 3,961 | 3,716–4,071 | 3,826 | 1.00× | – | – | – |

### All worker metrics (median, ratio vs baseline)

| metric | MLT |
|---|---:|
| busy incl. GC | 4,084 |
| &nbsp;&nbsp;of which GC | 102.4 |
| &nbsp;&nbsp;of which busy without GC | 3,961 |
| &nbsp;&nbsp;&nbsp;&nbsp;of which filtering (sampled, incl. callees) | 173.3 |
| &nbsp;&nbsp;&nbsp;&nbsp;of which timing instrumentation (sampled) | 144.8 |
| busy without GC and instrumentation | 3,816 |
| CPU time without GC | 1,015 |
| tile: download end → sent to main thread, median per tile | 3,866 |
| tile: download end → sent to main thread, 90th percentile | 3,915 |
| &nbsp;&nbsp;parse part (timing log, incl. waiting for glyphs/icons), median per tile | 782.5 |
| &nbsp;&nbsp;queue + hand-off part, median per tile | 1,725 |
| minor GCs | 7.00 |
| major GCs | 2.00 |
| peak worker heap (MB) | 32.6 |
| load: busy without GC | 750.8 |
| load: GC | 29.5 |
| total: busy without GC | 4,883 |

Rows marked *of which* are parts of the row above, not additional time. Tile rows are per-tile latencies (medians over tiles, then over runs), not sums: tiles overlap in time, and the medians of the parse and queue parts do not add up exactly to the median latency.

### Filtering (session window)

Sampled worker time spent in feature filtering, including everything the filter calls (expression evaluation, property access, lazy column decoding): **row filter** = the style-spec feature filter that MVT runs per feature, **mlt filter** = the columnar MLT filter (incl. the geometry-type selection). Medians per run; rules in `config/categories.toml`.

| variant | mlt filter | row filter | filtering total | ratio vs MLT | 95 % CI | MWU p | share of sampled busy |
|---|---:|---:|---:|---:|---:|---:|---:|
| MLT | 173.3 | 0.0 | 173.3 | 1.00× | – | – | 9.2% |

Top 12 functions inside filtering (self time, mean ms per run):

| phase | function | source | MLT |
|---|---|---|---:|
| mlt filter | `scanDictionaryCodes` | maplibre-tile-spec/ts/dist/processing/filter/execution/filterKernel.js | 19.8 |
| mlt filter | `filterByGeometryType` | maplibre-tile-spec/ts/dist/vector/geometry/geometryVector.js | 16.5 |
| mlt filter | `dictionaryRowMatches` | maplibre-tile-spec/ts/dist/processing/filter/execution/filterKernel.js | 15.0 |
| mlt filter | `resolveDictionaryExecutor` | maplibre-tile-spec/ts/dist/processing/filter/execution/filterKernel.js | 11.3 |
| mlt filter | `readValue` | maplibre-tile-spec/ts/dist/processing/filter/execution/filterKernel.js | 11.2 |
| mlt filter | `getDecodedLength` | maplibre-tile-spec/ts/dist/decoding/fsstDecoder.js | 5.1 |
| mlt filter | `decodeFastPforWithWorkspace` | maplibre-tile-spec/ts/dist/decoding/integerDecodingUtils.js | 5.0 |
| mlt filter | `decodeFastPfor` | maplibre-tile-spec/ts/dist/decoding/integerDecodingUtils.js | 4.2 |
| mlt filter | `(anonymous)` | maplibre-tile-spec/ts/dist/processing/filter/execution/filterKernel.js | 4.1 |
| mlt filter | `get numGeometries` | maplibre-tile-spec/ts/dist/vector/geometry/flatGeometryVector.js | 4.1 |
| mlt filter | `executeNode` | maplibre-tile-spec/ts/dist/processing/filter/execution/filterExecution.js | 3.9 |
| mlt filter | `resolveVectorExecutor` | maplibre-tile-spec/ts/dist/processing/filter/execution/filterKernel.js | 3.6 |

### Where the variants differ from MLT (session window, mean ms per run)

Open **[flame.html](flame.html)** to explore the call tree interactively: pick a variant, compare it with MLT (red = more time at the same call path, blue = less), click a frame to zoom in, and read the phase and function breakdown under it. `flame/*.txt` open in https://www.speedscope.app.

### Worker time by phase (session window, median ms of sampled self time)

| phase | MLT |
|---|---:|
| bucket row | 333.1 |
| bucket columnar | 265.2 |
| mlt decode | 178.5 |
| mlt filter | 173.3 |
| instrumentation | 144.8 |
| earcut | 133.4 |
| symbol layout | 131.4 |
| transfer | 101.1 |
| feature index | 97.5 |
| tile pipeline | 94.1 |
| style expressions | 83.5 |
| gc | 80.1 |
| mlt facade | 31.3 |
| runtime | 6.2 |
| other | 4.4 |
| row filter | 0.0 |
| pre-tess mesh | 0.0 |
| mvt decode | 0.0 |

### Top 20 worker functions by self time (session window, mean ms per run)

| function | source | phase | MLT |
|---|---|---|---:|
| `reserve` | src/util/struct_array.ts | bucket columnar | 86.1 |
| `addPhase` | src/source/worker_timing.ts | instrumentation | 83.4 |
| `(garbage collector)` | (native) | gc | 76.9 |
| `populate` | src/data/bucket/columnar/columnar_line_bucket.ts | bucket columnar | 65.4 |
| `emplace` | src/data/array_types.g.ts | bucket row | 48.6 |
| `insert` | src/data/feature_index.ts | feature index | 45.6 |
| `addLine` | src/data/bucket/line_bucket.ts | bucket row | 43.7 |
| `isEar` | node_modules/earcut/src/earcut.js | earcut | 37.8 |
| `parse` | src/source/worker_tile.ts | tile pipeline | 36.5 |
| `ProgramConfiguration` | src/data/program_configuration.ts | bucket row | 36.1 |
| `possiblyEvaluate` | src/style/properties.ts | style expressions | 34.2 |
| `addFeature` | src/data/bucket/line_bucket.ts | bucket row | 31.6 |
| `postMessage` | (native) | transfer | 29.9 |
| `addHalfVertex` | src/data/bucket/line_bucket.ts | bucket row | 25.4 |
| `populatePaintArrays` | src/data/program_configuration.ts | bucket row | 25.3 |
| `serialize` | src/util/web_worker_transfer.ts | transfer | 24.7 |
| `buildRingBoundingBoxes` | src/data/bucket/columnar/columnar_mesh_arrays.ts | bucket columnar | 24.5 |
| `materializeSelectedFeatures` | src/data/bucket/columnar/columnar_populate.ts | bucket columnar | 22.6 |
| `self.postMessage` | worker_hook.js | instrumentation | 21.6 |
| `get` | src/style/properties.ts | style expressions | 21.4 |

### Top 20 worker functions by total time (incl. callees) (session window, mean ms per run)

| function | source | phase | MLT |
|---|---|---|---:|
| `parse` | src/source/worker_tile.ts | tile pipeline | 1,678 |
| `loadTile` | src/source/vector_tile_worker_source.ts | tile pipeline | 1,559 |
| `_parseWorkerTile` | src/source/vector_tile_worker_source.ts | tile pipeline | 1,531 |
| `populate` | src/data/bucket/columnar/columnar_line_bucket.ts | bucket columnar | 748.2 |
| `populate` | src/data/bucket/columnar/columnar_fill_bucket.ts | bucket columnar | 378.5 |
| `addBucketFeatures` | src/data/bucket/fill_bucket.ts | bucket row | 269.7 |
| `addFeature` | src/data/bucket/columnar/columnar_fill_bucket.ts | bucket columnar | 266.6 |
| `writeEarcutFill` | src/data/bucket/columnar/columnar_mesh_arrays.ts | bucket columnar | 262.4 |
| `addFeature` | src/data/bucket/line_bucket.ts | bucket row | 242.1 |
| `addLine` | src/data/bucket/line_bucket.ts | bucket row | 179.4 |
| `selectColumnarFeatures` | src/data/bucket/columnar/columnar_populate.ts |  | 173.4 |
| `buildEarcutMesh` | src/data/bucket/columnar/columnar_mesh_arrays.ts | bucket columnar | 163.5 |
| `filterFeatureTable` | maplibre-tile-spec/ts/dist/processing/filter/execution/tableFilter.js |  | 156.6 |
| `executeNode` | maplibre-tile-spec/ts/dist/processing/filter/execution/filterExecution.js | mlt filter | 155.5 |
| `executeLeaf` | maplibre-tile-spec/ts/dist/processing/filter/execution/filterExecution.js | mlt filter | 148.0 |
| `earcut` | node_modules/earcut/src/earcut.js | earcut | 147.5 |
| `processTask` | src/util/actor.ts | transfer | 142.5 |
| `materializeSelectedFeatures` | src/data/bucket/columnar/columnar_populate.ts | bucket columnar | 132.0 |
| `executeAll` | maplibre-tile-spec/ts/dist/processing/filter/execution/filterExecution.js | mlt filter | 123.9 |
| `addFeatures` | src/data/bucket/symbol_bucket.ts | symbol layout | 121.7 |

### Tile parse time by zoom (timing log, median ms per tile, total − dependencies)

| zoom | MLT |
|---:|---:|
| 11 | 54.50 (n=36) |
| 12 | 176.00 (n=33) |
| 13 | 84.35 (n=24) |

### Tile latency by zoom: download end → result sent to the main thread (session window, median ms per tile)

Includes waiting in the worker's queue, the parse and posting the result; see `tile_latency.csv` for the per-tile split (`parse_ms`, `wait_ms`).

| zoom | MLT |
|---:|---:|
| 12 | 3,813 (n=33) |
| 13 | 1,008 (n=24) |

![session-smoke-worker-time](plots/session-smoke-worker-time.png)

![session-smoke-phases](plots/session-smoke-phases.png)

![session-smoke-tiles-by-zoom](plots/session-smoke-tiles-by-zoom.png)

## Runs

5 ok, 0 failed/aborted, 0 not run, 4 used in statistics.

## Validity checks

- Counted once: all 5 analysed runs pass (windows load + session + tail add up to total; phases add up to the sampled busy time; GC and sampled time lie within busy time; no timing-log line twice).
- session-smoke/mlt/rep-00: CPU samples cover only 50% of worker busy time
- session-smoke/mlt/rep-01: CPU samples cover only 66% of worker busy time
- session-smoke/mlt/rep-02: CPU samples cover only 47% of worker busy time
- session-smoke/mlt/rep-03: CPU samples cover only 42% of worker busy time
- session-smoke/mlt/rep-04: CPU samples cover only 46% of worker busy time
- runs were headless: the page renders in software on the CPU next to the worker, which inflates worker time and skips frames; do not compare with headed batches
- machine speed (calibration probe, rolling median over neighbouring runs) varied between 1.00× and 1.01× of the batch median (10th–90th percentile 1.00–1.01×)
- 4 run(s) where the probe changed by more than 15% between before and after the replay, so the adjustment is uncertain: session-smoke/mlt/rep-01 (0.48×), session-smoke/mlt/rep-02 (1.34×), session-smoke/mlt/rep-03 (0.63×), session-smoke/mlt/rep-04 (1.22×)
- spread within a variant (median IQR / median of busy without GC): raw 9.0%, load-adjusted 8.6%

## Files

- `runs.csv`: one row per run (incl. failed and warm-up runs), every scalar metric as `<window>.<metric>`.
- `summary.csv`: session × variant × metric statistics.
- `functions.csv`, `categories.csv`: CPU-sample self/total time per function and phase per run and window.
- `category_functions.csv`: self time per phase × function (e.g. what the filters spend their time on).
- `tiles.csv`, `tile_layers.csv`, `tile_phases.csv`: the per-tile worker timing log, long format.
- `flame.html`: interactive call tree per variant with a diff view; `flame/*.txt`: collapsed stacks for speedscope.
- `analysis/stacks.csv` (per run): sampled self time per full call stack.
- `tile_latency.csv`: per tile request, worker clock: received, download start/end, result sent, latency = sent − download end, parse_ms, wait_ms = latency − parse.
- `runs/<session>/<variant>/rep-NN/trace.json.gz`: the raw trace (opens in the DevTools Performance tab).
