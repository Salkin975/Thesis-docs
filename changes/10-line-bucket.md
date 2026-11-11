# 10. Line bucket

## The idea

Lines have no pre-tessellated shortcut: how many vertices a line produces depends on its joins, caps and
dashes, which are only known when it is extruded. So the columnar line bucket keeps `LineBucket`'s writing
entirely and changes only what comes before it: the selection runs on the columns, and only the selected rows
become features.

`ColumnarLineBucket` extends `LineBucket` and overrides `populate()`:

| Step | What it does |
|---|---|
| select | the filter on the columns, narrowed to LineStrings and Polygons ([page 8](08-populate-pipeline.md)) |
| prepare | features for the selected rows, with a `dashes` object and the data-driven `line-sort-key` |
| write and index | `LineBucket.addBucketFeatures()`, the method the row path calls |

## One write path for both

The second loop of `LineBucket.populate()` became the protected method `addBucketFeatures()`, the same shape
as `FillBucket`'s. It sorts by `line-sort-key`, registers pattern and dash images and parks the features that
wait for them, writes every other feature through `addFeature()`, and inserts it into the `FeatureIndex`.

`LineBucket.populate()` is now the row filter around this call, `ColumnarLineBucket.populate()` the columnar
selection around it. The columnar bucket has no copy of the write loop, the dash check or the dash-key
registration, so a change on `main` to any of them reaches both paths.

Two details are specific to MLT:

- **Clip columns.** `LineBucket` asks every feature for the `geojson-vt` clip properties, used to cut dashes
  and gradients at tile edges. On a row view each miss is a column lookup. The columnar bucket checks once per
  table whether the clip columns exist, and skips the per-feature question when they do not.
- **Pre-tessellated layers without rings** are skipped with one warning: triangles hold no line.

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

Splitting `addBucketFeatures()` out of `populate()` changed nothing measurable: in the NRW benchmark the gain
fell in a phase whose code did not change, and in browser session traces the line buckets' time per feature
moved by +1.9 % to +2.6 % in every format (Mann-Whitney p 0.60-0.75).

## In the code

Branch [`gl5-line-bucket`](https://github.com/Salkin975/maplibre-gl-js/compare/gl4-fill-bucket...gl5-line-bucket)
in maplibre-gl-js: `src/data/bucket/columnar/columnar_line_bucket.ts`, `addBucketFeatures()` in
`src/data/bucket/line_bucket.ts`, and `createBucket()` in `src/style/style_layer/line_style_layer.ts`. The clip
check came with [`gl7-performance-optimization`](https://github.com/Salkin975/maplibre-gl-js/compare/gl6-symbol-bucket...gl7-performance-optimization).
