# 13. How it was measured

## The benchmarks

Three benchmarks answer different questions. Each number on these pages names the one it comes from.

| Benchmark | Runs in | Measures | Used for |
|---|---|---|---|
| filter benchmark | Node | one tile from its unzipped bytes to the point where GL JS would write vertices: decoding, every style-layer filter once, the columns the bucket reads | the tile-spec changes (pages 1 to 5), the [`@maplibre/mlt` RFC](https://github.com/maplibre/maplibre-tile-spec/issues/2010) |
| session traces | Chromium | a recorded camera path replayed with tracing on: the worker's busy time, split by category and function from its CPU samples, plus heap and GC | the GL JS changes (pages 6 to 12), the [GL JS RFC](https://github.com/maplibre/maplibre-gl-js/issues/8985) |
| NRW parse benchmark | Node (vitest) | twelve z12 tiles of Cologne parsed through `WorkerTile.parse()`, summed by bucket and phase | before and after a single GL JS change |

Alongside them: a decode benchmark with an A/B runner that compares the working tree against the last commit
in alternating pairs of processes, and Node A/B scripts for single tile-spec changes.

## Three formats on the same tiles

- **MVT**: `@mapbox/vector-tile` and the style spec's per-feature filter, as in GL JS.
- **MLT**: plain MLT tiles, ring-encoded polygons.
- **Pre-tessellated MLT**: MLT tiles that also carry the triangles of their polygons.

The baseline for GL JS is `main` at `bb3895408` (26 October 2026) with `@maplibre/mlt` 1.3.0 from npm. The
baseline for the tile spec is its `main` at `71f20ee8`, read through GL JS `main`'s `MLTVectorTile`.

## The session traces

One 42 s session (z0 to z16) recorded with osm-bright, replayed with each style. Every batch runs one warm-up
round and then 10 rounds per variant, in rotating order, each in a fresh browser context. The headline metric
is worker busy time without garbage collection; a ratio is the ratio of medians with a bootstrap 95 %
confidence interval.

Rules learned while measuring, applied to every number:

| Rule | Reason |
|---|---|
| compare ratios inside one batch, never absolute times across days | MVT busy time was 10,770 ms one day and 6,865 ms three days later, with the same code |
| at least 10 runs for a ratio | single runs of identical code differ by about ±20 % |
| headed runs only | a headless browser renders in software; frames took 58 instead of 16.7 ms |
| check every MVT run for the `pbf` deopt storm | it once made MLT look like 0.73× MVT ([page 12](12-worker-performance.md)) |
| read the number of busy background cores per run | worker time rises by 210-300 ms per busy core |

The machine: a laptop with an AMD Ryzen 7 5800H, 32 GB RAM and an NVIDIA GeForce RTX 3060 Laptop GPU, Nobara
Linux 44, Chromium 156 from Playwright 1.64.1, headed, 1280×1024 viewport, device pixel ratio 1, one worker,
on AC power with the performance CPU governor.

## Correctness checks

| Check | Where |
|---|---|
| every filter job keeps the same features in MVT, MLT `main` and MLT, by feature id | filter benchmark, outside the clock |
| the style spec's filter test suites, ported, against the columnar engine | `mvtParity.spec.ts` in the tile spec |
| fill triangles, outline edges and index boxes equal `FillBucket`'s: 53 tiles, 166 polygon layers, 442,779 triangles | one-off script over NRW tiles |
| fill on the globe and in pole tiles byte-identical to `FillBucket` | `columnar_fill_bucket.test.ts` |
| the same symbol features, glyphs and icons from `ColumnarSymbolBucket` and `SymbolBucket` | `columnar_symbol_bucket.test.ts` |
| every feature of real tiles reads the same id, type, geometry and properties lazily as eagerly | `vector_tile_mlt.test.ts` |

## Limits

- **The timing log was on.** The GL JS session-trace batches ran with the worker timing log switched on. It
  costs about 1.5-3 % of worker time in every format. A batch with it off, on a production build, has not been
  run yet.
- **One region.** The tiles are OpenMapTiles-style tiles of North Rhine-Westphalia. Other schemas and regions
  were not measured.
- **Small layers are slower to filter.** The columnar filter has a fixed cost per filter, so on layers of
  fewer than about 50 features it is slower than MVT's row filter on its own
  ([page 2](02-filter-engine.md)).
- **Noise.** Run-to-run noise is about 10 % on a total in the decode benchmark and larger on small phases.
  The MVT variant, which no change touches, serves as a noise reference.
- **Plain fixtures differ from MVT in a few layers.** In the decode benchmark's plain MLT fixtures some layers
  hold different features than the MVT tile. Filters that disagreed were dropped, so the plain and the
  pre-tessellated sets time different filters and are not compared with each other.
- **Main-thread heap.** MLT keeps about 4 MB more on the main thread after GC, cause unknown
  ([page 12](12-worker-performance.md)).
- **One machine, one browser.** Firefox, Safari and mobile devices were not measured.
