# 1. Selection vectors

## The idea

A filter on columns does not produce features. It produces an answer to "which rows of this table match",
and every step after it (the next part of the filter, the geometry-type check, the bucket) narrows that
answer further. How that answer is stored decides how much a columnar filter costs.

Before, a selection was a `number[]` grown with `push()`. "Every row" had no representation of its own, so a
layer whose filter matches every row, such as a layer without a filter, still paid for an index array as
long as the layer. Now a `SelectionVector` has two forms:

- **`ConstSelectionVector`**: "all rows" or "no rows", stored as a flag and a length. It allocates nothing
  and cannot be changed.
- **`FlatSelectionVector`**: an explicit list of row indices in a `Uint32Array`, strictly ascending, without
  duplicates.

Ascending order makes an intersection a linear merge, and lets a selection describe its live part as a
prefix of its array (`limit`).

## The algebra

| Function | Produces |
|---|---|
| `createSelectionVector(size)` | every row, as a constant, with no allocation |
| `scanSelection(size, matches, selection?)` | the rows for which `matches(row)` holds; narrows `selection` in place when one is given |
| `unionSelectionVectors(vectors, totalSize)` | the union, through a `Uint8Array` presence mask |
| `intersectSelectionVectors(left, right)` | the intersection; a constant "all rows" operand returns the other side unchanged |
| `invertSelectionVector(selection, totalSize)` | the complement |

Every operation turns its result back into a constant when it covers all rows or none. That keeps the cheap
form reachable after an operation, not only when a selection is created, so a chain of operations does not
degrade into index lists.

```
table of 8 rows

union       {0, 2, 5} ∪ {1, 3, 4, 6, 7}   → mask full           → all rows (constant)
intersect   all rows ∩ {0, 2, 5}          → returned unchanged  → {0, 2, 5}
invert      no rows                                             → all rows (constant)
scan        in place     buffer [0 2 3 5 7], limit 5
            lanes > 2    buffer [2 5 7 · ·], limit 3            same Uint32Array
```

The in-place scan matters for filter chains: `["all", a, b, c]` narrows one buffer three times instead of
allocating three arrays. Where two branches need the same input (the children of an `any`), the filter
engine copies the selection for each; a constant is immutable and passed on without a copy.

## Geometry types without a scan

Most style layers draw only some geometry types: a line layer takes LineStrings and Polygons. MLT carries
geometry in two encodings, ring-encoded (`GeometryVector`) and pre-tessellated (`GpuVector`). Both now
implement one interface, `GeometryCollection`, with a `filter(geometryType)` that returns a selection vector.

- A source layer usually holds a single geometry type. Then `containsSingleGeometryType()` is true, and
  `filter()` answers "all rows" or "no rows" without looking at a single feature.
- Otherwise it scans once and still collapses to a constant if every or no feature matched.
- A multi-part type matches its single-part filter, as `$type` does in the style spec: `MULTIPOINT` sits three
  places after `POINT` in the type enumeration, so the test is `type === t || type === t + 3`.

## Reading one row

A columnar bucket reads only the rows its filter selected. Two column kinds could only be decoded whole:

- **Geometry.** `convertGeometryAtIndex(source, index)` decodes the rings of one feature. It follows the
  column's offsets from the feature to its parts, from a part to its rings, and from a ring to its vertices:

  | Array | Content | Meaning |
  |---|---|---|
  | `geometryOffsets` | `[0, 1, 3]` | feature 0 = polygon 0, feature 1 = polygons 1 and 2 |
  | `partOffsets` | `[0, 1, 3, 4]` | polygon 0 = ring 0, polygon 1 = rings 1 and 2, polygon 2 = ring 3 |
  | `ringOffsets` | `[0, 3, 7, 10, 14]` | ring 1 = vertices 3 to 6, ring 2 = vertices 7 to 9, ring 3 = vertices 10 to 13 |

  Reading feature 1 touches rings 1 to 3 and vertices 3 to 13. Feature 0 is not read.

- **Dictionary-encoded strings.** A dictionary column stores each distinct string once and a code per row.
  `getDictionaryValue(code)` decodes each distinct value once and caches it, so reading every row of a column
  with, say, 2,000 rows and 12 distinct values costs 12 string decodes instead of 2,000. Both row reads and the filter kernel go through this cache.

The dictionary and plain string vectors also expose their raw bytes and offsets, so the filter engine can
compare a string operand with the encoded bytes without decoding any string ([page 2](02-filter-engine.md)).

## What it is worth

Nothing on this page is timed on its own: the selection vectors are the data structure the filter engine and
the buckets are built from, and their effect is in those measurements. Two places where the constant form
shows directly:

- On a source layer of a single geometry type, the geometry-type selection of every line layer is a constant
  without a scan. GL JS also caches it per geometry vector, so the other style layers of the same source
  layer reuse it ([page 8](08-populate-pipeline.md)).
- The dictionary loop of the filter kernel returns a constant when all or no rows match, so later steps
  short-circuit ([page 5](05-decode-performance.md)).

## In the code

Branch [`feat1-vector-infrastructure`](https://github.com/Salkin975/maplibre-tile-spec/compare/main...feat1-vector-infrastructure),
in `ts/src/` of maplibre-tile-spec:

- `vector/filter/selectionVector.ts`, `constSelectionVector.ts`, `flatSelectionVector.ts`: the interface and
  its two forms (a third, `SequenceSelectionVector`, was deleted; the constant covers it).
- `vector/filter/selectionVectorUtils.ts`: the algebra.
- `vector/geometry/geometryCollection.ts`, `geometryVector.ts`, `gpuVector.ts`: the shared interface and
  `filterByGeometryType()`.
- `vector/geometry/geometryVectorConverter.ts`: `convertGeometryAtIndex()`.
- `vector/dictionary/stringDictionaryVector.ts`, `fsst-dictionary/stringFsstDictionaryVector.ts`: the
  per-code cache.
