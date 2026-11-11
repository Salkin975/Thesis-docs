# Results

## Worker time against MVT

Worker busy time without garbage collection in a recorded 42 s session (z0 to z16), replayed in Chromium, 10
runs per variant. Ratios of medians against MVT on `main` in the same batch, 95 % bootstrap confidence
interval in parentheses. `main` is GL JS `bb3895408`.

Three batches on 10 November, one per style, on one Windows workstation, compare `main` built with the
tile-spec changes (`@maplibre/mlt` at `85738fbf`, an earlier commit of the stack with all five changes) with
the GL JS changes on top. They show what the GL JS changes add. The column with `@maplibre/mlt` 1.3.0 is the
starting point before any change, from the 7 November batches on a Linux laptop.

| Style | MLT ÷ MVT, `main` with 1.3.0 | MLT ÷ MVT, `main` with the tile-spec changes | MLT ÷ MVT, all changes | pre-tess. MLT ÷ MVT, all changes | MLT speedup from the GL JS changes | pre-tess. MLT speedup from the GL JS changes |
|---|---|---|---|---|---|---|
| maptiler-basic | 1.30× (1.25-1.32) | 1.17× (1.15-1.19) | 0.91× (0.90-0.93) | 0.74× (0.72-0.75) | 1.29× | 1.61× |
| osm-bright | 1.22× (1.21-1.23) | 1.12× (1.10-1.15) | 0.91× (0.89-0.93) | 0.74× (0.72-0.75) | 1.23× | 1.55× |
| positron | not run | 1.19× (1.17-1.21) | 0.92× (0.90-0.93) | 0.78× (0.77-0.80) | 1.30× | 1.55× |

The speedups are the ratios of the medians of `main` and of the changes in the same batch, without a
confidence interval. Pre-tessellated MLT on `main` costs 1.15-1.22× MVT, because its triangles are thrown
away and computed again.

MVT costs the same with and without the changes (1.00×, 1.01× and 0.99×, every confidence interval inside
0.98-1.02): the MVT path is not slowed down by the row buckets' split.

![Worker busy time without GC relative to MVT on main, maptiler-basic](img/session-worker-time-ratio.png)

*maptiler-basic, 10 November. Every run is a dot, the bar is the geometric mean of the per-round ratios.
`dist` is GL JS with the changes, `main` is GL JS `main` with the tile-spec changes; all ratios are against
MVT on `main` in the same round.*

## Where it comes from

The maptiler-basic batch of 10 November, medians. `main` already has the tile-spec changes, so this is what
the GL JS changes add:

| | MVT, `main` | MLT, `main` | MLT, changes | pre-tess. MLT, `main` | pre-tess. MLT, changes |
|---|---|---|---|---|---|
| worker busy time without GC | 1,461 ms | 1,711 ms | 1,330 ms | 1,731 ms | **1,074 ms** |
| tile decoding | 127 ms | 196 ms | 110 ms | 218 ms | 138 ms |
| reading decoded data (feature objects, row views, facade) | – | 187 ms | 31 ms | 184 ms | 30 ms |
| fill and line buckets, incl. earcut | 602 ms | 602 ms | 505 ms | 595 ms | **235 ms** |
| memory freed by the worker's GCs | 1,421 MB | 1,544 MB | 1,051 MB | 1,554 MB | 570 MB |
| peak worker heap | 80 MB | 173 MB | 61 MB | 151 MB | **43 MB** |

![JS heap of the GL JS worker and the main thread over the session, maptiler-basic](img/session-heap.png)

*Worker heap over the 42 s session (left), 1 s rolling mean: on `main` (dashed) MLT climbs to about 140 MB
while MVT stays below 45 MB; with the changes (solid) every format stays within MVT's range.*

<details markdown>
<summary>Worker time by phase, all six variants</summary>

![Worker time by phase, maptiler-basic](img/session-phases.png)

*Median sampled self time per phase. The `main` bars for `mlt decode`, `mlt access`, `mlt facade` and
`bucket fill row`, and `earcut` for pre-tessellated tiles, are where the changes save most.*

</details>

| Gain | Comes from |
|---|---|
| decoding 196 → 110 ms | lazy layers and columns: a layer or column no style layer reads is not decoded. The decoder fixes are in both builds; with 1.3.0, `main` spent 426 ms here (7 November) |
| reading decoded data 187 → 31 ms | no feature object with copied properties per row; only the selected rows are read, through row views |
| fill and line buckets 602 → 505 ms, 235 ms pre-tessellated | triangles copied, earcut on the vertex buffer, only selected rows built |
| peak heap 173 → 61 MB | the release after each parse, and no per-feature objects with copied properties |
| filtering about equal to MVT's | the filter engine; the gain is not in filtering itself but in what is not built after it |

Filtering is a small part of the worker's time: 32 ms for MLT against 37 ms for MVT in the maptiler-basic
batch, plus 21 ms for decoding the columns the filters read first, which MVT spends in its own decoding.
Symbol layout and transfer cost about the same in every format, the feature index about a third less with
the changes (50 → 33 ms).

## What it costs in size

Both packages built from their committed trees at the baseline and at the head of each stack
(`@maplibre/mlt` `71f20ee8` → `feat5-decode-performance`, GL JS `bb3895408` with `@maplibre/mlt` 1.3.0 →
`gl7-performance-optimization` with the tile-spec head). Sizes in bytes; gzip at the default level, the way
GL JS's `build/check-bundle-size.ts` measures its bundles.

**What a GL JS user downloads.** The production bundles, `npm run build-prod`:

| Bundle | | `main` | changes | difference |
|---|---|---|---|---|
| `maplibre-gl-worker.mjs` | minified | 519,352 | 554,889 | +35,537 (+6.8 %) |
| | gzip | 148,324 | 159,359 | **+11,035 (+7.4 %)** |
| | brotli | 121,465 | 130,296 | +8,831 (+7.3 %) |
| `maplibre-gl.mjs` | minified | 1,107,256 | 1,141,124 | +33,868 (+3.1 %) |
| | gzip | 296,233 | 306,613 | **+10,380 (+3.5 %)** |
| | brotli | 241,216 | 249,282 | +8,066 (+3.3 %) |

The main-thread bundle grows too, because it holds the bucket classes (for deserializing the transferred
buckets) and an `MLTVectorTile` for `queryRenderedFeatures`.

Where the growth of the worker bundle comes from, minified bytes split by source file through the source map:

| Source | `main` | changes | difference |
|---|---|---|---|
| `@maplibre/mlt` | 65,852 | 87,086 | +21,234 |
| GL JS `src/data/bucket/columnar/` | 0 | 9,372 | +9,372 |
| GL JS `src/source/vector_tile_mlt.ts` | 886 | 3,356 | +2,470 |
| GL JS `src/source/worker_timing.ts` | 0 | 1,172 | +1,172 |
| GL JS, the rest of `src/` (bucket splits, dispatch) | 240,731 | 241,969 | +1,238 |
| other dependencies | 210,797 | 210,802 | +5 |

About 60 % of the growth is the tile spec, about 40 % GL JS. `worker_timing.ts` is the benchmark timing log
(off by default); without it the worker bundle grows by about 34 KB minified.

**`@maplibre/mlt` on its own.** The whole public API bundled with tree shaking and minified (dependencies
external), and what the npm package ships in `dist/`:

| | `71f20ee8` | `feat5-decode-performance` | difference |
|---|---|---|---|
| public API, minified | 80,970 | 102,447 | +21,477 (+26.5 %) |
| public API, gzip | 21,336 | 27,299 | **+5,963 (+27.9 %)** |
| `dist/` JavaScript, unminified | 374,372 | 440,054 | +65,682 (+17.5 %) |
| `dist/` type declarations | 73,065 | 86,803 | +13,738 (+18.8 %) |

The public API includes the encoder, which GL JS does not import; that is why GL JS carries 66-87 KB of the
package and not 81-102 KB.

**Source lines**, without tests:

| Package | before | after | difference | per change |
|---|---|---|---|---|
| `@maplibre/mlt` `ts/src/` | 11,462 | 13,420 | +1,958 (+17.1 %) | selection vectors +354, filter engine +1,022, lazy decoding +363, adapter primitives +94, decode performance +125 |
| GL JS `src/` | 72,780 | 74,173 | +1,393 (+1.9 %) | facade +92, dispatch +42, populate pipeline +120, fill bucket +693, line bucket +74, symbol bucket +98, worker performance +274 |

The filter engine is half of the tile-spec growth, the fill bucket half of the GL JS growth
(`columnar_mesh_arrays.ts` alone is 476 lines). Tests and benchmarks add another 1,949 lines to the tile spec
and 1,833 to GL JS.

The GL JS baseline uses `@maplibre/mlt` 1.3.0 from npm, the tile-spec baseline is `71f20ee8`, as in the
7 November benchmarks. The two are not byte-identical, so the package's growth inside the worker bundle (+21,234) and on
its own (+21,477) are measured against slightly different baselines. The tile-spec head is the committed
branch, without uncommitted work in the submodule.

## How it was measured

| Benchmark | Runs in | Measures | Used for |
|---|---|---|---|
| filter benchmark | Node | one tile from unzipped bytes to the point where GL JS would write vertices | the `@maplibre/mlt` changes |
| session traces | Chromium, headed | a recorded camera path replayed with tracing on: worker busy time by category and function, heap, GC | the GL JS changes, the numbers above |
| NRW parse benchmark | Node (vitest) | twelve z12 tiles of Cologne through `WorkerTile.parse()` | before and after a single GL JS change |

Three formats on the same OpenMapTiles-style tiles of North Rhine-Westphalia: MVT, plain MLT, and
pre-tessellated MLT. Ratios are compared only inside one batch, with at least 10 runs, because absolute times
of identical code moved by a third between days on the same machine. The details and the rules learned while
measuring are on [how it was measured](../changes/13-measuring.md).

## Limits

- **Two machines.** The batches with the changes ran on a Windows 11 workstation (Core Ultra 9 285K); the
  1.3.0 baseline only exists from a Ryzen 7 5800H laptop on Linux. No ratio is formed across the two.
- **Timing log.** The 10 November batches ran without the worker timing log (off by default); the 7 November
  batches behind the 1.3.0 column had it on, about 1.5-3 % of worker time in every format.
- **One region, one schema.** NRW tiles in the OpenMapTiles schema. Other schemas were not measured.
- **One browser.** Chromium only, driven by Playwright. Firefox, Safari and mobile were not measured.
- **Small layers.** On source layers with fewer than about 50 features the columnar filter alone is slower
  than the row filter, because planning and resolving kernels is a fixed cost per filter.
- **Main-thread heap.** At the end of the replay the main thread holds about 2-5 MB more with MLT than with
  MVT, with wide confidence intervals; cause unknown.

All batches and their plots are in the [benchmark reports](../changes/benchmarks/index.md).
