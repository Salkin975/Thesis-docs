# 5. Decode performance

## The idea

Measure first, then change what the measurement shows is large, one change at a time, each judged by its own
measurement. Two rounds were made. The first measured the decoder on its own in Node. The second took its
targets from where a GL JS worker spends its time in a real map session in Chromium
([page 12](12-worker-performance.md)).

## Round one: where the decoder spent its time

A full decode of a plain MLT tile, per tile, on ten fixture tiles of North Rhine-Westphalia:

| Phase | Time | Share |
|---|---|---|
| property columns | 5.7 ms | about 70 % |
| geometry | 2.0 ms | about 24 % |
| metadata and column walk | 0.24 ms | about 3 % |
| ids | 0.16 ms | about 2 % |
| **end to end** | **8.1 ms** | |

Earlier performance work had targeted the metadata; it is 3 % of the total, so nothing done there can matter
much. A CPU profile showed the real cost: `createDecoderWorkspace` of the FastPFOR integer decoder, with
**56.6 %** of the self time. `decodeFastPfor()` created a new workspace, about 64 KiB of zero-filled buffers,
for every FastPFOR-encoded stream it decoded, and a tile has one such stream per FastPFOR-encoded column.

| Change | What it does |
|---|---|
| A: one shared FastPFOR workspace | Created on first use, reused for every stream. Decoding is synchronous and each worker has its own module instance, so two calls never share it at the same time |
| B: `readVarint()` in the metadata decoders | A single header value was read through a stream decoder that allocated a typed array per call |
| C: `releaseDecodedColumns()` | Puts a table back into its lazy state ([page 3](03-lazy-decoding.md)): decoded columns dropped, column offsets kept |

Results (A and B against the previous commit, alternating pairs of runs, per tile):

| Phase | Plain tiles | Pre-tessellated tiles |
|---|---|---|
| properties | -80 % | -70 % |
| geometry | -54 % | -12 % (noisy) |
| metadata | -40 % | -16 % |
| allocation, full decode | -54 % | -59 % |
| **end to end** | **-70 %** (18.6 → 4.0 ms) | **-45 %** (11.1 → 5.1 ms) |

And the release (C), after a full decode of all columns:

| Tiles | Retained after decode | After release | Release takes | Decoding everything again |
|---|---|---|---|---|
| plain | 500 KB | 29 KB (-94 %) | 0.05 ms | 2.66 ms |
| pre-tessellated | 680 KB | 33 KB (-95 %) | 0.06 ms | 2.62 ms |

Built, measured and removed again, because the measurement did not justify them: a cache of decoded layer
schemas (the metadata is about 1 % of the decode), a per-schema plan of column kinds, skipping streams without
reading their headers, a one-pass assembly of stream metadata, and an ASCII fast path for strings.

## Round two: what the browser showed

Session traces of GL JS in Chromium sum the worker's CPU samples per function. On an osm-bright session the
largest tile-spec costs were the per-row loop that every filter kernel shared, one closure call per row,
64-bit ids decoded as `BigInt`, and per-row bit reads for missing values. Each change below was measured with
an A/B script over twelve z12 tiles of Cologne, old and new bundle alternating, 150 rounds each:

| Change | What it does | Result |
|---|---|---|
| D: decoding fast paths, a number kernel | One pass for RLE plus delta, no copies where a typed array can be reinterpreted, raw-array comparison for one number operand | no separate measurement |
| E: bit reads with shifts | `index >> 3` and `index & 7` instead of `Math.floor(index / 8)` and `index % 8` (below) | osm-bright filters 18-21 → 15-17 ms per round |
| F: a loop for dictionary columns | Its own loop over the codes, reading the present bits as bytes, negation folded into the code table, constants where the result is all or nothing | 18-21 → 7-9 ms per round, the same 27,128 features |
| G: encoded operands cached | String operands UTF-8-encoded once per filter for the whole session, not once per tile | MLT filtering about 830 → 390 ms in a one-run trace |
| H: `unpackNullable` a byte at a time | Skips eight missing values at once | 98-125 → 64-101 µs on 20,000 positions |
| I: safe 64-bit ids as numbers | Ids decoded as doubles when every value is a safe integer, as `bigint` otherwise | decoding and reading the ids 2.3-3.0 → 0.5-0.6 ms |
| J: short strings in JavaScript | Layer and column names below 12 bytes decoded by a JS loop instead of `TextDecoder` | metadata 410 → 92 µs per parsed tile in Chromium |
| K: TypeScript `private` instead of `#private` | Compiled for ES2020, `#private` fields became `WeakMap` lookups | `decodeTile()` alone 7.4-9.1 → 3.2-5.7 ms per pass in Node |

Change I removes `decodeTile()`'s `idWithinMaxSafeInteger` parameter, which is a breaking change for a caller
that passed it. With the safe-integer check the parameter only chose where rounding happens.

### Example: one bit per row

A nullable column carries a bitmap of which rows have a value: one bit per row, eight rows per byte, least
significant bit first. Every nullable column reads it once per row, in the filter and when it is expanded.

```
row 13      byte 13 >> 3 = 1, bit 13 & 7 = 5
bitmap      byte 0: 1011 0111   byte 1: 0010 0110
                                          ^ bit 5 is 1: row 13 has a value

before      Math.floor(13 / 8) = 1, 13 % 8 = 5   a double, a floor, a float remainder
after       13 >> 3 = 1, 13 & 7 = 5              two 32-bit integer instructions
```

Both forms give the same result for every row index from 0 to 2^31 - 1.

### Example: is this id safe?

A varint above 2^53 - 1 cannot be held exactly as a double, but it always reads as at least 2^53, and so does a
delta sum that leaves the safe range. One `value <= Number.MAX_SAFE_INTEGER` test per decoded value therefore
catches every id that lost precision. If any fails, the stream is decoded again as `bigint`s. All 105 long id
columns of the twelve Cologne tiles decode as numbers, with identical values.

## What it is worth

In GL JS session traces of the same osm-bright session, MLT filtering went from 2.06× to 1.26× the time of
MVT's filter with Changes D to I. Counted apart from the column decoding it triggers (which MVT does in its own
decoding step), the filtering itself is now equal to MVT's: 0.97× in a maptiler-basic session (86 against
89 ms), 0.89× in an osm-bright session (336 against 378 ms).

Offline in Node, the tile-spec decoder decodes the tiles of an osm-bright session 2-2.7× faster than
`@mapbox/vector-tile`. Less of that shows in Chromium; [page 12](12-worker-performance.md) explains what was
found and what is still open.

## In the code

Branch [`feat5-decode-performance`](https://github.com/Salkin975/maplibre-tile-spec/compare/feat4-adapter-primitives...feat5-decode-performance),
in `ts/src/` of maplibre-tile-spec:

- `decoding/fastPforDecoder.ts`: the shared workspace (A).
- `vector/featureTable.ts`, `vector/lazyPropertyVectors.ts`: `releaseDecodedColumns()` (C), TS `private` (K).
- `processing/filter/execution/filterKernel.ts`: the number kernel and the dictionary loop (D, F, G).
- `vector/flat/bitVector.ts`, `decoding/unpackNullableUtils.ts`: bit reads and unpacking (E, H).
- `decoding/integerStreamDecoder.ts`, `decoding/idColumnDecoder.ts`: safe 64-bit ids (I).
- `decoding/decodingUtils.ts`, `mltDecoder.ts`: short strings (J).

The benchmark tooling is in the [benchmarking repository](https://github.com/Salkin975/Maplibre-benchmarking)
(`decode-bench/`, `session-trace-bench/`).
