# 7. Dispatch and worker hand-off

## The idea

A tile can serve columnar and row buckets at the same time. Whether a style layer is built columnar depends
only on that layer: an MLT tile, and a filter the engine can plan at the current zoom. A layer whose filter
cannot be planned falls back on its own and does not take the other layers with it. The worker then hands
each bucket the input it accepts: the MLT layer for a columnar bucket, the usual row list for a row bucket.

## Choosing the bucket

Each style layer's `createBucket()` asks the filter engine:

```ts
createBucket(parameters: BucketParameters<any>): FillBucket {
    return isColumnarBucketSupported(parameters.encoding, this.filter, parameters.zoom, this.id)
        ? new ColumnarFillBucket(parameters)
        : new FillBucket(parameters);
}
```

`isColumnarBucketSupported()` answers from the cached plan of [page 2](02-filter-engine.md), so the question
costs a lookup after the first tile. Fill, line and symbol layers have a columnar bucket. Circle, heatmap and
fill-extrusion layers have none and always take the row path.

Three additions make the hand-off possible:

- `BucketParameters.encoding` says how the **parsed** source layer is encoded: `'mlt'` if it has a feature
  table, `'mvt'` otherwise.
- `Bucket.isColumnar` marks a bucket that reads columns.
- `Bucket.populate()` accepts either the row list or an `MLTVectorTileLayer`.

## Handing over the input

```ts
const mltLayer = isMLTVectorTileLayer(sourceLayer) ? sourceLayer : undefined;
let mltRows: IndexedFeature[] | undefined;
// … per style layer of this source layer:
// MVT: the row list, as before
let populateFeatures: IndexedFeature[] | MLTVectorTileLayer = features;
if (mltLayer) {
    populateFeatures = bucket.isColumnar ?
        mltLayer :
        (mltRows ??= mltLayer.indexedFeatures(getId, sourceLayerIndex));
}
bucket.populate(populateFeatures, options, canonical);
```

For an MLT layer the row list is built only if a row bucket asks for it, and only once: if every bucket of a
source layer is columnar it is never built, and if several row buckets share the source layer they share one
list. The `bucket.isColumnar` test stays at the call site, because a layer whose filter could not be planned
gets a row bucket although its tile is MLT.

## The overzoom fix

`encoding` used to describe the request, not the parsed tile, and on overzoom the two differ:

| Step | State |
|---|---|
| `new WorkerTile(params)` | `encoding = 'mlt'` from the request |
| `loadVectorTile()` | a real `MLTVectorTile` |
| overzoom | the tile is cut and **re-encoded as MVT**, `encoding` stays `'mlt'` |
| `createBucket()` | sees `'mlt'`, builds a **columnar** bucket |
| `bucket.populate()` | gets the row list |

Rendering stayed correct, because a columnar bucket given rows falls back to its parent's `populate()`, but
the columnar path was silently lost for an MLT source shown past its maximum zoom. `encoding` is now set from the
parsed layer, which makes the rule hold: a columnar bucket always gets an MLT layer.

## Giving the columns back

The worker keeps a tile's `MLTVectorTile` after the parse, because `reloadTile()` parses from it again. Without
a release every column the parse touched would stay decoded for as long as the tile is loaded. `parse()`
therefore ends with:

```ts
// after addFeatures() of every bucket
if (data instanceof MLTVectorTile) data.releaseDecodedColumns();
```

| Decision | Reason |
|---|---|
| after the last `addFeatures()`, not after `populate()` | symbol features read columns until their glyphs and images have arrived; releasing earlier would decode them again within the same parse |
| only for `MLTVectorTile` | an overzoomed tile is MVT and holds only an index |
| a reload decodes again | about 2.6 ms per tile for all columns ([page 5](05-decode-performance.md)) |

## What it is worth

The release is what brings MLT's worker memory below MVT's. In the maptiler-basic session traces the peak
worker heap is 201 MB for MLT on `main` and 61 MB with the changes, against 67 MB for MVT; the memory freed by
the worker's garbage collections falls from 1,627 to 1,059 MB ([overview](index.md)).

## In the code

Branch [`gl2-dispatch`](https://github.com/Salkin975/maplibre-gl-js/compare/gl1-mlt-facade...gl2-dispatch)
in maplibre-gl-js: `src/data/bucket.ts`, `src/source/worker_tile.ts`, and `indexedFeatures()` in
`src/source/vector_tile_mlt.ts`. Tested in `src/source/worker_tile_dispatch.test.ts` on a real MLT tile. The
`createBucket()` of each style layer lands with its bucket (pages 9 to 11).
