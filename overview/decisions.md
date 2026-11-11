# Decisions and open questions

## The rules behind the design

| Rule | Why |
|---|---|
| **Same result as MVT.** | A columnar path that draws different features is a bug, not an optimization. The style spec's filter tests run against the engine, the benchmarks compare selected features by id, and the fill output is compared with `FillBucket`'s triangle by triangle. |
| **A whole filter or none.** | A partly applied filter draws wrong features. A filter is planned completely or rejected before any tile is touched; a rejected layer takes the row path, with one warning naming the part that failed. |
| **Inherit, do not copy.** | Every columnar bucket extends its row bucket and replaces only the selection. Writing, sorting, deferral and indexing exist once, so a change on `main` reaches both paths. |
| **Pay only for what is read.** | Layers, columns and rows are decoded or built on first use, and given back after the parse. |
| **No format, renderer or shader change.** | The work is confined to the worker and the decoder; the `main` decoder reads the same tiles. |

## Trade-offs taken

| Trade-off | Accepted because |
|---|---|
| A decoded table keeps the tile buffer alive | GL JS keeps the raw tile bytes for reloads anyway |
| A corrupt column is reported on first read | the header walk still fails on a misaligned offset, close to its cause |
| The earcut fill path writes about 5 % more vertices | skipping `subdividePolygon()`'s deduplication is its largest saving; triangles and outlines are the same |
| The globe and pole tiles use `FillBucket` | the direct paths do not subdivide; globe keeps the row path's cost and exact output |
| A fill layer without ring topology draws no outline | the triangles alone carry no ring; the bucket warns once |
| The filter alone is slower on layers below about 50 features | a fixed cost per filter; decoding and filtering together stay below MVT at every zoom |
| A reload decodes the columns again | about 2.6 ms per tile, against about 470 KB less retained memory per tile |
| `decodeTile()` loses `idWithinMaxSafeInteger` | ids are numbers whenever every value is safe; the parameter only chose where rounding happens |

## Built, measured and not kept

| Idea | Why not |
|---|---|
| A point-free copy of `LineBucket`'s extrusion | byte-identical and 1/1.4 the allocation, but run time within noise; estimated 15-20 ms per session against about 200 copied lines to keep in step with `main` |
| A cache of decoded layer schemas, a per-schema plan of column kinds | the metadata is about 1-3 % of the decode |
| Skipping streams without reading their headers, one-pass stream metadata, an ASCII string fast path | the measurement did not justify them |
| A per-tile cache of filter leaf selections and kernels | most leaves differ in their operands; lookups and copies cancelled the savings, net within noise |

## Open questions for maintainers

From the two RFCs:

1. **Layers without ring topology.** A pre-tessellated fill layer without ring offsets draws no outline. Is a
   warning enough, or should the encoder keep ring topology for drawn layers?
2. **Splitting the row buckets.** `FillBucket`, `LineBucket` and `SymbolBucket` get `populate()` split into
   protected methods. Is this an acceptable seam in shared code?
3. **Lazy decoding.** A decoded table keeps the tile buffer alive, and corrupt columns surface late. Is that
   acceptable for `@maplibre/mlt`'s other consumers?
4. **PR shape.** Stacked PRs that follow the changes, with the fill bucket landing first in GL JS since it
   carries the largest gain?

Still unmeasured or unexplained: symbol `populate` on osm-bright (old evidence predates a deopt fix), resolving
symbol text on the columns, the main-thread heap difference, and a production build without the timing log.

## The branch stacks

Each change is a branch in a fork, stacked on the one before, so each compare link shows only that change.

| Repository | Branches, in order |
|---|---|
| maplibre-tile-spec | `feat1-vector-infrastructure` → `feat2-filter-engine` → `feat3-lazy-decoding` → `feat4-adapter-primitives` → `feat5-decode-performance` |
| maplibre-gl-js | `gl1-mlt-facade` → `gl2-dispatch` → `gl3-populate-pipeline` → `gl4-fill-bucket` → `gl5-line-bucket` → `gl6-symbol-bucket` → `gl7-performance-optimization` |

The compare links for every branch are on the [explainer overview](../changes/index.md#where-the-code-is).
The RFCs: [`@maplibre/mlt`](https://github.com/maplibre/maplibre-tile-spec/issues/2010), [GL JS](https://github.com/maplibre/maplibre-gl-js/issues/8985).
