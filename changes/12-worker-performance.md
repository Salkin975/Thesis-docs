# 12. Worker performance

## The idea

Pages 1 to 11 make the MLT path columnar. Whether that makes a map faster is decided in the worker of a real
browser session, not in a micro-benchmark. So the MLT path was measured where it runs: a recorded camera path
replayed in Chromium with tracing on, the worker's busy time split into categories and functions from its CPU
samples ([how it was measured](13-measuring.md)). The MLT-specific costs were ranked by their share of the
worker time, and the large and cheap ones removed, each change judged by a new batch of runs.

At the start, on a 37 s osm-bright session, plain MLT cost 1.17× the worker time of MVT.

## What was found, and what was done

| Found | Cost | Done |
|---|---|---|
| the filter's per-row loop, closures, bit reads, `BigInt` ids | `scanSelection` 74 ms, kernel closures 64 ms, `decodeVarintInt64Value` 52 ms per session | dedicated loops, safe ids as numbers ([page 5](05-decode-performance.md)) |
| transferring MLT buckets took far longer than MVT's, for the same payload | `serialize` 330 against 132 ms | a deoptimization storm, fixed in one line (below) |
| fill in Mercator still ran the subdivision bookkeeping | about 330 ms per maptiler-basic session | earcut on the vertex buffer ([page 9](09-fill-bucket.md)) |
| geometry built twice per vertex: the package's point, then GL JS's | NRW parse 1,257 ms per round (osm-bright) | read straight from the vertex buffer: 1,121 ms ([page 6](06-mlt-facade.md)) |
| a `TextDecoder` call per layer and column name | 32-37 ms, the largest function inside `decodeTile()` | short strings decoded in JavaScript ([page 5](05-decode-performance.md)) |
| `#private` fields compiled to `WeakMap` lookups | about 25 ms per maptiler-basic session | TS `private` ([page 5](05-decode-performance.md)) |
| symbol `populate` on osm-bright took about twice MVT's time | 786 against 400 ms | not done: the evidence predates the deopt fix below, and on maptiler-basic symbol layout is equal; to be measured again |

## Example: one line, thousands of deoptimizations

MLT spent 330 ms in `serialize` against MVT's 132 ms, and 109 ms in `FeaturePositionMap.add` against 2 ms, for
the same payload. Chromium logged 1,700 to 13,300 worker deoptimizations per MLT run, against a few hundred
for MVT, most of them "wrong name" at a `for...in` loop over the paint program configurations, inlined into
`FillBucket.addFeature`.

The cause was the facade's `tile.layers`. It was a plain `{}` whose layers start as getters and turn into data
properties on first read ([page 6](06-mlt-facade.md)). That reconfiguration changes hidden classes V8 shares
with every object created from `{}`, among them the objects keyed by style layer ids that the `for...in` loop
walks. Its fast path was compiled for one key and thrown away on the next, over and over. Node did not
reproduce it; only Chromium did.

```ts
layers: Record<string, VectorTileLayerLike> = Object.create(null);   // was: {}
```

| 3 runs, osm-bright | MVT | MLT before | MLT after |
|---|---|---|---|
| `serialize` | 132 ms | 330 ms | 125 ms |
| `FeaturePositionMap.add` | 2 ms | 109 ms | 3 ms |
| transfer phase | 676 ms | 883 ms | 629 ms |
| feature index phase | 237 ms | 396 ms | 213 ms |
| worker deoptimizations per run | 160-244 | 1,700-13,300 | 176-556 |

Two other explanations were tried first and reverted, because neither changed `serialize`.

## Where the time goes now

A 21 s maptiler-basic session, batch `20261022-144914`, medians of 10 runs in ms (the medians of the
categories do not add up to the median of the total):

| Category | MVT | MLT | pre-tessellated MLT |
|---|---|---|---|
| decoding (MVT's, or MLT's outside the filter) | 369 | 247 | 264 |
| columns decoded by the filter | 0 | 69 | 53 |
| filtering | 89 | 86 | 73 |
| reading decoded data, facade | 0 | 84 | 70 |
| row buckets | 1,024 | 423 | 356 |
| columnar buckets | 0 | 393 | 155 |
| earcut | 545 | 475 | 2 |
| pre-tessellated meshes | 0 | 0 | 34 |
| symbol layout | 606 | 649 | 529 |
| transfer to the main thread | 277 | 270 | 217 |
| feature index | 117 | 88 | 56 |
| garbage collection | 202 | 156 | 123 |
| **busy without GC** | **3,896** | **3,674** | **2,547** |

- Decoding and filtering together cost MLT 407 ms against MVT's 457 (0.89×). The filtering itself is equal.
- Fill and line buckets: MVT 1,569 ms (row buckets and earcut), plain MLT 1,291, pre-tessellated MLT 547.
- Symbol layout is a shared phase that does not depend on the format; its spread between variants is noise.
- MLT allocates less: the worker's garbage collections free 871 MB (MLT) and 501 MB (pre-tessellated) against
  1,287 MB for MVT.

This batch is older than the numbers on the [overview](index.md), which come from the later batches of the
[GL JS RFC](https://github.com/maplibre/maplibre-gl-js/issues/8985), with a 42 s session and all three styles.

## Found along the way

- **A deoptimization storm in MVT.** Some MVT runs hit a deopt loop in `pbf`'s `readSVarint`: about 5,500 to
  6,000 worker deopts instead of about 240, and 3 to 4 s more busy time per 37 s session. It hit no MVT run in
  one batch and every MVT run in another, on byte-identical code, so it is not caused by the changes. Every MVT
  run is checked for it; affected runs are reported, not silently dropped.
- **The decoder is faster in Node than it looks in Chromium.** Offline in Node, the tile spec decodes the 187
  tiles of an osm-bright session 2-2.7× faster than `@mapbox/vector-tile`. In Chromium, MLT's decoding came out
  above MVT's. A `TextDecoder` call per short string and the `#private` helpers were causes and are removed.
  Deopts, JIT warm-up and columns decoded twice were ruled out.
- **Main-thread heap.** After its last GC the main thread keeps about 4 MB more JS heap with MLT than with MVT
  (19.2 against 14.8 MB), although MLT transfers 5 % less tile data. The cause is not known yet; it is an open
  question of the [GL JS RFC](https://github.com/maplibre/maplibre-gl-js/issues/8985).

## In the code

Branch [`gl7-performance-optimization`](https://github.com/Salkin975/maplibre-gl-js/compare/gl6-symbol-bucket...gl7-performance-optimization)
in maplibre-gl-js: the fix in `src/source/vector_tile_mlt.ts`, the pipeline and line-bucket changes in
`src/data/bucket/columnar/`, the worker timing log in `src/source/worker_timing.ts` (off by default), and the
NRW parse benchmark in `src/source/worker_tile_nrw.bench.ts`. The fill work lives on `gl4-fill-bucket`, the
tile-spec changes on `feat5-decode-performance`. The session trace tool is in the
[benchmarking repository](https://github.com/Salkin975/Maplibre-benchmarking).
