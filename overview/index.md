# Columnar MLT in MapLibre, in five minutes

## The problem

GL JS reads an MLT tile through `MLTVectorTile`. On `main` its constructor decodes every column of every layer
and calls `getFeatures()` on each layer, which builds a JavaScript object with copied properties for every
feature. From there an MLT tile takes the MVT path: the style filter runs per feature as a generic
expression, every polygon is triangulated with earcut, and the decoded columns stay in memory for as long as
the tile is loaded.

So the format's columnar layout is turned back into rows before anything is drawn. With `@maplibre/mlt`
1.3.0, MLT costs **1.22-1.30× the worker time of MVT** and reaches about **three times its peak worker
heap**. Pre-tessellated tiles bring nothing, because their triangles are thrown away and computed again.

## The idea

Let the worker filter and build buckets on the columns, and decode only what it reads:

- A style filter is planned once and evaluated per tile as a scan over typed columns. Its result is a
  selection vector, "which rows", and only those rows ever become features.
- Layers, columns and properties are decoded on first read. A layer no style layer draws is never decoded
  past its name.
- Pre-tessellated polygons are copied into the vertex arrays as they are. Plain polygons run earcut on the
  vertex buffer, without a `Point` per vertex.
- After each parse the worker gives the decoded columns back.

## The result

Worker busy time without GC in a recorded 42 s map session (z0 to z16), replayed in Chromium, 10 runs per
variant, against MVT:

| Style | MLT, `main` with 1.3.0 | MLT, `main` with the tile-spec changes only | MLT with all changes | pre-tessellated MLT with all changes |
|---|---|---|---|---|
| maptiler-basic | 1.30× | 1.17× | 0.91× | 0.74× |
| osm-bright | 1.22× | 1.12× | 0.91× | 0.74× |
| positron | not run | 1.19× | 0.92× | 0.78× |

The first column is from 7 November batches on a Linux laptop, the other three from batches on 10 November on
a Windows workstation; ratios are only compared inside one batch.

The tile-spec changes alone leave MLT slower than MVT, because GL JS `main` still builds a feature object per
row. With the GL JS changes MLT becomes the cheaper format and pre-tessellated MLT the cheapest. The peak worker
heap on maptiler-basic falls from 173 MB to 61 MB (MVT: 64-80 MB; 201 MB on `main` with 1.3.0).

The price is code size: the gzipped worker bundle grows by 11 KB (+7.4 %), the main bundle by 10 KB (+3.5 %),
about 60 % of it from `@maplibre/mlt`. The breakdown of both is on [results](results.md).

## What changes, and what does not

| Changes | Does not change |
|---|---|
| `@maplibre/mlt`: selection vectors, a columnar filter engine, lazy column decoding, adapter primitives, decoder speedups | the MLT format, and the tiles the `main` decoder reads |
| GL JS worker: a lazy MLT facade, per-layer dispatch, columnar fill, line and symbol buckets | the renderer, the shaders, the main thread |
| `FillBucket`, `LineBucket`, `SymbolBucket`: `populate()` split into protected methods, lines moved, not rewritten | MVT tiles, which run the existing code unchanged |
| | circle, heatmap and fill-extrusion layers, which keep the row path |

A style layer whose filter the engine cannot plan falls back to its row bucket on its own, with one warning.
The other layers of the tile stay columnar.

## Reading this site

| Page | Answers |
|---|---|
| [How a tile is parsed](architecture.md) | the worker's path through a tile, before and after, and what each package owns |
| [@maplibre/mlt](mlt-package.md) | what the package gains, its new API and what behaves differently |
| [MapLibre GL JS](gl-js.md) | what changes in the worker, and which existing files are touched |
| [Results](results.md) | where the time and memory go, how it was measured, the limits |
| [Decisions and open questions](decisions.md) | the rules behind the design, the trade-offs, what is still open, the PR stacks |

Each page links to the explainer page of every change, which has the detail, the measurements and the code
([all explainer pages](../changes/index.md)). The full proposals are the two RFCs,
[`@maplibre/mlt`](https://github.com/maplibre/maplibre-tile-spec/issues/2010) and [GL JS](https://github.com/maplibre/maplibre-gl-js/issues/8985).
