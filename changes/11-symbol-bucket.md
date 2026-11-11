# 11. Symbol bucket

## The idea

The shortest of the buckets. A symbol bucket's `populate()` writes no vertices: it resolves each feature's
text and icon and registers the glyphs and images it needs. The layout happens later in
`performSymbolLayout()`, once the worker has the glyphs, and symbols are not entered into the spatial index.
So the columnar symbol bucket replaces only the selection, and hands every selected feature to
`SymbolBucket`'s own code.

## Splitting `SymbolBucket.populate()`

`SymbolBucket.populate()` was one loop: evaluate the filter, skip point labels whose points all lie outside
the tile, resolve text and icon, register glyphs and images, then merge lines and sort. A subclass could
override the whole method but reuse nothing inside it. It is now split into protected methods whose bodies
are the lines of the former loop, moved:

| Method | Does | Runs |
|---|---|---|
| `layoutHasText()`, `layoutHasIcon()` | whether the layer draws text, and whether it has an icon | once per `populate()` |
| `addSymbolFeature(...)` | load the geometry, skip a point label outside the tile, resolve text and icon, register glyphs and images | per selected feature |
| `finishSymbolFeatures()` | `mergeLines()` for line placement, then sort by the sort key | once per `populate()` |

`SymbolBucket.populate()` is the row filter around these calls. `ColumnarSymbolBucket.populate()` is the
columnar selection around the same calls: for each selected row it reads the feature from the layer, resolves
the id through `featureIndex.getId()` so `promoteId` applies, and calls `addSymbolFeature()`.

- **Sorting stays at the end.** `mergeLines()` can still change the feature list, so the drawing order is
  decided after it, not by the selection order.
- **`sourceLayerIndex` is transferred.** Symbol queries use it on the main thread, so this bucket keeps it in
  the transfer, unlike the fill and line buckets.

## Touching MVT code

The split changes the row `SymbolBucket`, though only by moving lines. The existing symbol tests and the
parity tests (the same features, glyphs and icons from both buckets, with and without a filter, with a
data-driven sort key, and with merged lines) check that both paths stay identical. In return, a change on
`main` to the per-feature steps reaches both: rebasing onto `main` brought three such changes (glyph variants,
vertical forms, point labels outside the tile), each of which a copy would have had to follow by hand.

## What it is worth

Measured in browser session traces before and after the split (maptiler-basic, 5 runs per build and format),
as time per feature relative to the fill buckets of the same run, to cancel out the machine's load:

| Format | Symbol bucket time per feature | Mann-Whitney p |
|---|---|---|
| MLT | -21.6 % | 0.01 |
| pre-tessellated MLT | -20.7 % | 0.01 |
| MVT | +6.2 % | 0.60, within noise |

`ColumnarSymbolBucket.populate()` went from 204 to 123 ms per run: the bucket's former per-feature code of its
own gave way to the shared `addSymbolFeature()`.

Open: whether resolving text on the columns, instead of per prepared feature, would help symbol layers has not
been evaluated.

## In the code

Branch [`gl6-symbol-bucket`](https://github.com/Salkin975/maplibre-gl-js/compare/gl5-line-bucket...gl6-symbol-bucket)
in maplibre-gl-js: `src/data/bucket/columnar/columnar_symbol_bucket.ts`, the split in
`src/data/bucket/symbol_bucket.ts`, and `createBucket()` in `src/style/style_layer/symbol_style_layer.ts`.
