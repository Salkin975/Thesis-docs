# 10. Line bucket

## The idea

Lines have no pre-tessellated shortcut: how many vertices a line produces depends on its joins, caps and
dashes, which are only known when it is extruded. So the columnar line path keeps `LineBucket`'s writing
entirely and changes only what comes before it: the selection runs on the columns, and only the selected rows
become features.

`LineBucket.populate()` takes either the row list or an MLT layer. Given a layer, it calls
`populateColumnarLine()`, a standalone function that gets the bucket, the layer, the options and the tile:

| Step | What it does |
|---|---|
| select | the filter on the columns, narrowed to LineStrings and Polygons |
| prepare | features for the selected rows, with a `dashes` object and the data-driven `line-sort-key` ([page 8](08-populate-pipeline.md)) |
| write and index | `LineBucket.addBucketFeatures()`, the method the row path calls |

## Selecting lines

A line layer draws LineStrings and Polygons, and not the points a source layer may also hold.
`selectLineFeatures()` intersects the filter's selection with the geometry column's LineString and Polygon
features.

- **Once per table.** Finding those features is a scan over the whole geometry column, and every line layer
  of a source layer draws from the same ones. The result is cached per geometry vector, so the other line
  layers reuse it.
- **Pre-tessellated tables** hold polygons only, so the filter's selection is already the answer and the scan
  is skipped.

## One write path for both

`addBucketFeatures()` holds everything a line feature goes through after it has been selected. It sorts by
`line-sort-key`, registers pattern and dash images and parks the features that wait for them, writes every
other feature through `addFeature()`, and inserts it into the `FeatureIndex`.

`LineBucket.populate()` calls it after its row filter, `populateColumnarLine()` after the columnar selection.
There is one copy of the write loop, the dash check and the dash-key registration, so a change on `main` to
any of them reaches both paths.

Two details are specific to MLT:

- **Clip columns.** `LineBucket` asks every feature for the `geojson-vt` clip properties, used to cut dashes
  and gradients at tile edges. On a row view each miss is a column lookup. `populateColumnarLine()` checks
  once per table whether the clip columns exist and sets `bucket.hasLineClipColumns`; `lineFeatureClips()`
  skips the per-feature question when it is false. A bucket that is populated from rows always asks.
- **Pre-tessellated layers without rings** are skipped with one warning: triangles hold no line. A line layer
  over such a source layer is skipped before its bucket is created when its filter cannot be planned
  ([page 7](07-dispatch.md)).

`hasLineClipColumns` and the other fields only the worker reads are kept out of the transfer to the main
thread ([page 8](08-populate-pipeline.md)).

## What was planned and not built

The first plan was a point-free copy of `LineBucket.addLine()`, the extrusion, with every normal and vertex as
a pair of numbers instead of a `Point` object. Measured on a prototype, it produced byte-identical output and
reduced allocation to about 1/1.4, but its run time stayed within noise, because short-lived objects are cheap
in V8's young generation. From the session traces, a point-free write path was estimated to save 15-20 ms
per maptiler-basic session, against about 200 lines of extrusion code to copy and keep in step with `main`.
It was not built.

## What it is worth

The gain comes only from selection and from not building the features the filter drops, so line layers
benefit least, and least of all where the filter keeps most features. The pipeline changes of
[page 8](08-populate-pipeline.md) took columnar line `populate` in the NRW parse benchmark from 587 to 454 ms
for osm-bright and from 538 to 350 ms for positron, so writing and indexing lines cost what they cost for MVT.

Sharing `addBucketFeatures()` between the paths costs nothing measurable: in the NRW benchmark the gain fell
in a phase whose code did not change, and in browser session traces the line buckets' time per feature moved
by +1.9 % to +2.6 % in every format (Mann-Whitney p 0.60-0.75).

## In the code

Branch [`gl8-review-feedback`](https://github.com/Salkin975/maplibre-gl-js/tree/gl8-review-feedback)
in maplibre-gl-js:

- `src/data/bucket/columnar/columnar_line.ts`: `populateColumnarLine()` and `selectLineFeatures()`.
- `src/data/bucket/line_bucket.ts`: `populate()`, `addBucketFeatures()`, `hasLineClipColumns` and
  `lineFeatureClips()`.
- `src/data/bucket/columnar/columnar_line.test.ts`: the tests against the row path, for the joins and caps.
