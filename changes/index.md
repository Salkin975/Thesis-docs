# Columnar MLT in MapLibre GL JS

These pages explain what the thesis changes, and why. A MapLibre Tile (MLT) stores each layer column by
column: one column for the ids, one for the geometry, one per property. MapLibre GL JS on `main` throws that
layout away. Its worker decodes every column of every layer, builds a JavaScript object for every feature,
runs the style filter on each object, and triangulates every polygon with earcut, even when the tile already
carries the triangles. An MLT tile is turned back into rows before anything is drawn, and ends up slower than
the Mapbox Vector Tile (MVT) it is meant to replace.

The changes let the worker filter and build buckets directly on the columns. They sit in two codebases:

- **`@maplibre/mlt`** (maplibre-tile-spec, TypeScript decoder): selection vectors, a columnar filter engine,
  lazy column decoding, the primitives an adapter needs, and decoder performance (pages 1 to 5).
- **MapLibre GL JS**: an MLT facade, per-layer dispatch, and columnar fill, line and symbol buckets that reuse
  the row buckets' code (pages 6 to 12).

The tile format, the renderer and the shaders do not change. MVT tiles, and every layer that cannot use the
columnar path, run the existing code unchanged.

## Results

The worker time, memory, tile sizes and bundle sizes, measured against `main`, are on the overview's
[results](../overview/results.md) page. How they were measured is on [how it was measured](13-measuring.md).

## How the changes build on each other

Each style layer of a tile goes through the same steps. The numbers in brackets are the pages below.

```mermaid
flowchart TD
    bytes["MLT tile bytes"]
    scan["Block scan (4)<br/>name and byte range<br/>of every layer"]
    layer["Lazy layer (6)<br/>decoded on first read,<br/>column headers only"]
    dispatch{"Dispatch (7)<br/>filter plannable<br/>at this zoom?"}
    row["Row bucket<br/>existing code,<br/>one warning per filter"]
    plan["Filter plan (2)<br/>built once per filter,<br/>cached"]
    select["Select (1, 2, 8)<br/>run the plan<br/>on the columns"]
    cols["Lazy columns (3)<br/>only the columns<br/>something reads"]
    prepare["Prepare (8)<br/>features for the<br/>selected rows only"]
    fill["Fill (9)<br/>copy the tile's triangles<br/>or earcut on the vertex buffer"]
    line["Line (10)"]
    symbol["Symbol (11)<br/>text, icons, glyphs"]
    write["Write and index<br/>the row bucket's own code"]
    release["Release (5, 7)<br/>decoded columns dropped<br/>after the parse"]

    bytes --> scan --> layer --> dispatch
    dispatch -->|"no"| row
    dispatch -->|"yes"| plan --> select
    cols -.->|"decoded on<br/>first access"| select
    select -->|"SelectionVector"| prepare
    prepare --> fill
    prepare --> line
    prepare --> symbol
    fill --> write
    line --> write
    symbol --> release
    write --> release
    row --> release
```

- Nothing is decoded before it is needed. A tile is split into layers without decoding them, a layer is
  decoded to its column headers on first read, and a column's data on first access.
- A filter is planned once and then evaluated per tile as a scan over typed columns. Its result, a
  [selection vector](01-selection-vectors.md), says which rows survive, and nothing else is built for the rows
  that do not.
- Writing vertices, sorting and the spatial index stay in the row buckets. The columnar buckets inherit from
  them and call the same methods, so both paths draw the same features.

## One layer, end to end

A line layer of a zoom-14 MLT tile with eight features and the columns `id`, geometry, `class`, `lanes`,
`surface` and `name`, all of its features LineStrings. The style layer filters it with

```json
["all", ["==", "class", "primary"],
        ["any", [">", "lanes", 2], ["==", "surface", "paved"]]]
```

```
1 wrap      scanLayerBlocks()            names and byte ranges, nothing decoded
2 decode    first read of the layer      column headers walked, offsets kept
3 dispatch  isColumnarBucketSupported()  filter plannable at z14
                                         → ColumnarLineBucket, plan cached
4 select    class == 'primary'           dictionary, once per value  {0,2,3,5,7}
            any: lanes > 2               Int32, its copy of the 5    {2,5,7}
                 surface == 'paved'      dictionary, its copy        {0,2,7}
                 union, within the 5                                 {0,2,5,7}
            geometry type                only LineStrings → all rows, no scan
5 prepare   features 0, 2, 5 and 7       properties are row views, not copies
6 write     addBucketFeatures()          LineBucket's code: sort, dashes, index
7 release   after the last addFeatures() decoded columns dropped

decoded      class, lanes, surface, geometry, id
not decoded  name, and every layer that no style layer reads
```

The filter engine page walks through step 4 in detail ([filter engine](02-filter-engine.md)).

## Rules every change follows

- **Same result as MVT.** The style spec's filter test suite runs against the columnar engine, the benchmarks
  compare the selected features by id, and the fill bucket's triangles, outline edges and index boxes equal
  `FillBucket`'s on 53 tiles of North Rhine-Westphalia (166 polygon layers, 442,779 triangles). The one
  difference in the written data: the earcut fill path does not deduplicate vertices and writes about 5 %
  more of them, for the same triangles and outlines.
- **A whole filter or none.** A filter is planned completely or rejected before any tile is touched. A
  rejected layer takes the existing row path, with one warning per filter naming the part that failed. The
  other layers of the tile are not affected.
- **Inherit, do not copy.** Every columnar bucket extends its row bucket and overrides only the selection. The
  row buckets' `populate()` is split into protected methods so both paths call the same writing code.
- **Pay only for what is read.** Layers, columns and rows are decoded or built on first use.
- **No format, renderer or shader change.** The current `main` decoder reads the same tiles, and
  `getFeatures()` returns the same result as before.

## The pages

**`@maplibre/mlt`**

1. [Selection vectors](01-selection-vectors.md): "which rows" without an index array where possible.
2. [Filter engine](02-filter-engine.md): style filters planned once, evaluated on columns.
3. [Lazy decoding](03-lazy-decoding.md): a column is decoded when it is first read.
4. [Adapter primitives](04-adapter-primitives.md): block scan, row view and 64-bit values in the package.
5. [Decode performance](05-decode-performance.md): what the decoder spent its time on, and releasing columns.

**MapLibre GL JS**

6. [MLT facade](06-mlt-facade.md): an MLT tile that looks like any other vector tile.
7. [Dispatch and hand-off](07-dispatch.md): columnar or row bucket, per style layer.
8. [Shared populate pipeline](08-populate-pipeline.md): select and prepare once for every bucket.
9. [Fill bucket](09-fill-bucket.md): pre-tessellated triangles copied, earcut on the vertex buffer.
10. [Line bucket](10-line-bucket.md): columnar selection, `LineBucket`'s writing.
11. [Symbol bucket](11-symbol-bucket.md): columnar selection, `SymbolBucket`'s code.
12. [Worker performance](12-worker-performance.md): what the session traces found, and what was fixed.

**Method**

13. [How it was measured](13-measuring.md): the benchmarks, the machine and the limits.

## Where the code is

Every change is a branch in a fork. The branches form one stack per repository, each on the one before it,
so each link below shows only that change.

| Page | Repository | Branch |
|---|---|---|
| 1 | maplibre-tile-spec | [`feat1-vector-infrastructure`](https://github.com/Salkin975/maplibre-tile-spec/compare/main...feat1-vector-infrastructure) |
| 2 | maplibre-tile-spec | [`feat2-filter-engine`](https://github.com/Salkin975/maplibre-tile-spec/compare/feat1-vector-infrastructure...feat2-filter-engine) |
| 3 | maplibre-tile-spec | [`feat3-lazy-decoding`](https://github.com/Salkin975/maplibre-tile-spec/compare/feat2-filter-engine...feat3-lazy-decoding) |
| 4 | maplibre-tile-spec | [`feat4-adapter-primitives`](https://github.com/Salkin975/maplibre-tile-spec/compare/feat3-lazy-decoding...feat4-adapter-primitives) |
| 5 | maplibre-tile-spec | [`feat5-decode-performance`](https://github.com/Salkin975/maplibre-tile-spec/compare/feat4-adapter-primitives...feat5-decode-performance) |
| 6 | maplibre-gl-js | [`gl1-mlt-facade`](https://github.com/Salkin975/maplibre-gl-js/compare/main...gl1-mlt-facade) |
| 7 | maplibre-gl-js | [`gl2-dispatch`](https://github.com/Salkin975/maplibre-gl-js/compare/gl1-mlt-facade...gl2-dispatch) |
| 8 | maplibre-gl-js | [`gl3-populate-pipeline`](https://github.com/Salkin975/maplibre-gl-js/compare/gl2-dispatch...gl3-populate-pipeline) |
| 9 | maplibre-gl-js | [`gl4-fill-bucket`](https://github.com/Salkin975/maplibre-gl-js/compare/gl3-populate-pipeline...gl4-fill-bucket) |
| 10 | maplibre-gl-js | [`gl5-line-bucket`](https://github.com/Salkin975/maplibre-gl-js/compare/gl4-fill-bucket...gl5-line-bucket) |
| 11 | maplibre-gl-js | [`gl6-symbol-bucket`](https://github.com/Salkin975/maplibre-gl-js/compare/gl5-line-bucket...gl6-symbol-bucket) |
| 12 | maplibre-gl-js | [`gl7-performance-optimization`](https://github.com/Salkin975/maplibre-gl-js/compare/gl6-symbol-bucket...gl7-performance-optimization) |

The full proposals are the two RFCs, [`@maplibre/mlt`](https://github.com/maplibre/maplibre-tile-spec/issues/2010) and
[GL JS](https://github.com/maplibre/maplibre-gl-js/issues/8985).
