# 7. Dispatch and worker hand-off

## The idea

A tile can serve columnar and row buckets at the same time. Whether a style layer is built columnar depends
only on that layer: an MLT tile, and a filter the engine can plan at the current zoom. A layer whose filter
cannot be planned falls back on its own and does not take the other layers with it. The worker then hands
each bucket the input it accepts: the MLT layer for a columnar bucket, the usual row list for a row bucket.

## Deciding in the constructor

`createBucket()` builds the same bucket as for MVT: a `FillBucket`, `LineBucket` or `SymbolBucket`. The bucket
decides for itself, in its constructor, whether it populates from columns:

```ts
this.isColumnar = isColumnarBucket(options);
```

```ts
export function isColumnarBucket({encoding, layers, zoom}: BucketParameters<TypedStyleLayer>): boolean {
    return isColumnarBucketSupported(encoding, layers[0].filter, zoom, layers[0].id);
}
```

`isColumnarBucketSupported()` answers from the cached plan of [page 2](02-filter-engine.md), so the question
costs a lookup after the first tile. Fill, line and symbol layers have a columnar path. Circle, heatmap and
fill-extrusion buckets never set `isColumnar` and always take the row path.

Three additions make the hand-off possible:

- `BucketParameters.encoding` says how the **parsed** source layer is encoded: `'mlt'` if it has a feature
  table, `'mvt'` otherwise.
- `Bucket.isColumnar` marks a bucket that reads columns. The three buckets above are its only setters.
- `Bucket.populate()` accepts either the row list or an `MLTVectorTileLayer`. It is the input that selects the
  path: a bucket given a row list populates from the rows, whatever `isColumnar` says.

## Handing over the input

```ts
const mltLayer = isMLTVectorTileLayer(sourceLayer) ? sourceLayer : undefined;
let mltRows: IndexedFeature[] | undefined;
// … per style layer of this source layer:
// MVT: the row list
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

## Pre-tessellated layers without rings

A pre-tessellated source layer can be stored without ring topology: it holds triangles only. Its row view has
no rings to give, only the triangles, each as a ring of its own, so a row bucket would draw the outline of
every triangle: a line layer would draw them as lines.

Only a columnar bucket can draw such a layer correctly. So `parse()` skips every style layer over it that no
columnar bucket draws, with one warning per layer:

- fill, line and symbol layers whose filter cannot be planned on the columns, checked before their bucket is
  created, so the constructor's own warning does not fire as well,
- every circle, heatmap and fill-extrusion layer.

A line layer whose filter can be planned is skipped as well, by the columnar line path, because triangles hold
no line. A pre-tessellated layer stored with rings keeps the row path, which reads its real rings.

## The encoding of the parsed layer

`encoding` describes the parsed layer, not the request, and on overzoom the two differ:

| Step | State |
|---|---|
| `new WorkerTile(params)` | the request says MLT |
| `loadVectorTile()` | a real `MLTVectorTile` |
| overzoom | the tile is cut and **re-encoded as MVT** |
| `parse()` | its layers have no feature table, so `encoding` is `'mvt'` |
| bucket constructor | `isColumnar` is false |
| `bucket.populate()` | gets the row list |

Taken from the request, `encoding` would be `'mlt'` for an overzoomed tile, and its buckets would be columnar
yet receive rows. Taken from the layer, the rule holds: a columnar bucket always gets an MLT layer.

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

Branch [`gl8-review-feedback`](https://github.com/Salkin975/maplibre-gl-js/tree/gl8-review-feedback)
in maplibre-gl-js:

- `src/data/bucket.ts`: `BucketParameters.encoding`, `Bucket.isColumnar` and the `populate()` signature.
- `src/data/bucket/columnar/columnar_populate.ts`: `isColumnarBucket()`; it is called by the constructors of
  `src/data/bucket/fill_bucket.ts`, `line_bucket.ts` and `symbol_bucket.ts`.
- `src/source/worker_tile.ts`: the hand-over, the skip rule and the release; `indexedFeatures()` in
  `src/source/vector_tile_mlt.ts`.
- Tested in `src/source/worker_tile_dispatch.test.ts` on a real MLT tile, and for each bucket's decision in
  `columnar_fill.test.ts`, `columnar_line.test.ts` and `columnar_symbol.test.ts`.
