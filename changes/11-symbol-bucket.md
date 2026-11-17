# 11. Symbol bucket

## The idea

The shortest of the buckets. A symbol bucket's `populate()` writes no vertices: it resolves each feature's
text and icon and registers the glyphs and images it needs. The layout happens later in
`performSymbolLayout()`, once the worker has the glyphs, and symbols are not entered into the spatial index.
So the columnar symbol path replaces only the selection, and hands every selected feature to
`SymbolBucket`'s own code.

## The steps of `SymbolBucket.populate()`

`SymbolBucket.populate()` evaluates the filter, skips point labels whose points all lie outside the tile,
resolves text and icon, registers glyphs and images, then merges lines and sorts. These steps are public
methods of the bucket:

| Method | Does | Runs |
|---|---|---|
| `layoutHasText()`, `layoutHasIcon()` | whether the layer draws text, and whether it has an icon | once per `populate()` |
| `addSymbolFeature(indexedFeature, evaluationFeature, hasText, hasIcon, options, canonical)` | load the geometry, skip a point label outside the tile, resolve text and icon, register glyphs and images | per selected feature |
| `finishSymbolFeatures()` | `mergeLines()` for line placement, then sort by the sort key | once per `populate()` |

`SymbolBucket.populate()` takes either the row list or an MLT layer. For a row list it is the row filter
around these calls. For a layer it calls `populateColumnarSymbol()`, a standalone function that is the
columnar selection around the same calls: for each selected row it reads the feature from the layer, resolves
the id through `featureIndex.getId()` so `promoteId` applies, and passes the feature with its id and index
to `addSymbolFeature()` as one `IndexedFeature`.

- **Sorting stays at the end.** `mergeLines()` can still change the feature list, so the drawing order is
  decided after it, not by the selection order.
- **`sourceLayerIndex` is transferred.** Symbol queries use it on the main thread, so this bucket keeps it in
  the transfer, unlike the fill and line buckets. Only `isColumnar` stays in the worker.

## Sharing MVT code

The row `SymbolBucket` and the columnar path run the same methods. The existing symbol tests and the parity
tests (the same features, glyphs and icons from both paths, with and without a filter, with a data-driven
sort key, with merged lines and with `promoteId`) check that both stay identical. A change on `main` to the
per-feature steps reaches both: rebasing onto `main` brought three such changes (glyph variants, vertical
forms, point labels outside the tile), each of which a copy would have had to follow by hand.

## What it is worth

Measured in browser session traces (maptiler-basic, 5 runs per build and format), as time per feature
relative to the fill buckets of the same run, to cancel out the machine's load. The comparison is between a
columnar symbol path with per-feature code of its own and the one that shares `addSymbolFeature()`:

| Format | Symbol bucket time per feature | Mann-Whitney p |
|---|---|---|
| MLT | -21.6 % | 0.01 |
| pre-tessellated MLT | -20.7 % | 0.01 |
| MVT | +6.2 % | 0.60, within noise |

The columnar symbol populate went from 204 to 123 ms per run: the former per-feature code of its own gave
way to the shared `addSymbolFeature()`.

Open: whether resolving text on the columns, instead of per prepared feature, would help symbol layers has not
been evaluated.

## In the code

Branch [`gl8-review-feedback`](https://github.com/Salkin975/maplibre-gl-js/tree/gl8-review-feedback)
in maplibre-gl-js:

- `src/data/bucket/columnar/columnar_symbol.ts`: `populateColumnarSymbol()`.
- `src/data/bucket/symbol_bucket.ts`: `populate()` and the methods above.
- `src/data/bucket/columnar/columnar_symbol.test.ts`: the tests against the row path.
