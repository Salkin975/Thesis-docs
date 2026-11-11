# Benchmark reports

Every benchmark report behind the numbers on these pages, unedited, as the tools wrote them.

- **[Filter benchmark](filter-bench.md)**: the Node benchmark from `benchmarking/filter-bench` (decode + filter per tile, 30 October 2026).
- **Session traces**: the GL JS worker-time benchmark from `benchmarking/session-trace-bench`. Each run has a report, its plots and an interactive worker flame graph. See [How it was measured](../13-measuring.md) for the method.

Early runs were used to develop the tool and to chase noise; later runs supersede them. Runs up to 6 November 12:02 ran on a Windows laptop (Intel i7-1365U); runs from 6 November 16:10 through 8 November ran on the Linux laptop described in [How it was measured](../13-measuring.md) (AMD Ryzen 7 5800H). The three runs on 10 November ran on a Windows workstation (Intel Core Ultra 9 285K); see [Hardware, 10 November](session-trace/2026-11-10-hardware.md). Each report names its machine. The headline column is the worker busy time without GC in the session window, as a ratio against MVT on the same build (lower is better). Runs that compare several branch builds list them under *builds*; their per-build ratios are in the report.

## Session traces

| run | style | builds | busy without GC vs MVT | flame graph |
|---|---|---|---|---|
| [2026-11-10 14:16 · maptiler-basic](session-trace/20261110-141627/report.md) | maptiler-basic (recorded: osm-bright) | main | MLT 0.91×, MLT tessellated 0.74× | [flame](session-trace/20261110-141627/flame.html) |
| [2026-11-10 12:11 · positron](session-trace/20261110-121157/report.md) | positron (recorded: osm-bright) | main | MLT 0.92×, MLT tessellated 0.78× | [flame](session-trace/20261110-121157/flame.html) |
| [2026-11-10 10:52 · osm-bright](session-trace/20261110-105247/report.md) | osm-bright | main | MLT 0.91×, MLT tessellated 0.74× | [flame](session-trace/20261110-105247/flame.html) |
| [toner](session-trace/toner/report.md) | toner (recorded: maptiler-basic) | – | MLT 0.95×, MLT tessellated 0.69× | [flame](session-trace/toner/flame.html) |
| [kernel-coverage](session-trace/kernel-coverage/report.md) | kernel-coverage (recorded: maptiler-basic) | – | MLT 0.87×, MLT tessellated 0.58× | [flame](session-trace/kernel-coverage/flame.html) |
| [2026-11-08 16:30 · maptiler-basic](session-trace/20261108-163052/report.md) | maptiler-basic | main--mlt-1-3-0 | MLT 0.94×, MLT tessellated 0.77× | [flame](session-trace/20261108-163052/flame.html) |
| [2026-11-07 17:15 · maptiler-basic](session-trace/20261107-171557/report.md) | maptiler-basic | main--mlt-1-3-0 | MLT 0.93×, MLT tessellated 0.77× | [flame](session-trace/20261107-171557/flame.html) |
| [2026-11-07 15:46 · maptiler-basic](session-trace/20261107-154620/report.md) | maptiler-basic | main--mlt-1-3-0 | MLT 0.94×, MLT tessellated 0.78× | [flame](session-trace/20261107-154620/flame.html) |
| [2026-11-07 14:29 · positron](session-trace/20261107-142945/report.md) | positron | – | MLT 0.92×, MLT tessellated 0.81× | [flame](session-trace/20261107-142945/flame.html) |
| [2026-11-07 13:56 · maptiler-basic](session-trace/20261107-135632/report.md) | maptiler-basic | – | MLT 0.94×, MLT tessellated 0.79× | [flame](session-trace/20261107-135632/flame.html) |
| [2026-11-07 13:19 · osm-bright](session-trace/20261107-131921/report.md) | osm-bright | – | MLT 0.89×, MLT tessellated 0.80× | [flame](session-trace/20261107-131921/flame.html) |
| [2026-11-07 12:54 · maptiler-basic](session-trace/20261107-125455/report.md) | maptiler-basic | – | MLT 0.95×, MLT tessellated 0.76× | [flame](session-trace/20261107-125455/flame.html) |
| [2026-11-07 12:37 · positron](session-trace/20261107-123741/report.md) | positron | – | MLT 0.92×, MLT tessellated 0.83× | [flame](session-trace/20261107-123741/flame.html) |
| [2026-11-07 12:16 · osm-bright](session-trace/20261107-121656/report.md) | osm-bright | – | MLT 0.92×, MLT tessellated 0.80× | [flame](session-trace/20261107-121656/flame.html) |
| [2026-11-06 19:51 · osm-bright](session-trace/20261106-195111/report.md) | osm-bright | – | MLT 0.92×, MLT tessellated 0.81× | [flame](session-trace/20261106-195111/flame.html) |
| [2026-11-06 16:52 · osm-bright](session-trace/20261106-165233/report.md) | osm-bright | main, main--mlt-1-3-0 | MLT 0.92×, MLT tessellated 0.78× | [flame](session-trace/20261106-165233/flame.html) |
| [2026-11-06 16:10 · osm-bright](session-trace/20261106-161007/report.md) | osm-bright | – | MLT tessellated 0.77× | [flame](session-trace/20261106-161007/flame.html) |
| [2026-11-06 12:02 · osm-bright](session-trace/20261106-120229/report.md) | osm-bright | – | MLT 0.96×, MLT tessellated 0.82× | [flame](session-trace/20261106-120229/flame.html) |
| [2026-11-06 11:54 · osm-bright](session-trace/20261106-115437/report.md) | osm-bright | – | MLT 0.91×, MLT tessellated 0.81× | [flame](session-trace/20261106-115437/flame.html) |
| [2026-11-06 10:38 · osm-bright](session-trace/20261106-103822/report.md) | osm-bright | – | MLT 1.02×, MLT tessellated 0.85× | [flame](session-trace/20261106-103822/flame.html) |
| [2026-11-06 10:32 · osm-bright](session-trace/20261106-103225/report.md) | osm-bright | – | MLT 0.81×, MLT tessellated 1.06× | [flame](session-trace/20261106-103225/flame.html) |
| [2026-11-06 10:13 · osm-bright](session-trace/20261106-101306/report.md) | osm-bright | – | MLT 0.93×, MLT tessellated 0.76× | [flame](session-trace/20261106-101306/flame.html) |
| [2026-11-03 09:34 · osm-bright](session-trace/20261103-093411/report.md) | osm-bright | – | MLT 0.88×, MLT tessellated 0.70× | [flame](session-trace/20261103-093411/flame.html) |
| [2026-11-03 09:19 · osm-bright](session-trace/20261103-091957/report.md) | osm-bright | gl7-performance-optimization | MLT 0.97×, MLT tessellated 0.99× | [flame](session-trace/20261103-091957/flame.html) |
| [2026-11-02 13:00 · osm-bright](session-trace/20261102-130002/report.md) | osm-bright | gl7-before-splits, gl7-performance-optimization | MLT 0.73×, MLT tessellated 0.62× | [flame](session-trace/20261102-130002/flame.html) |
| [2026-10-29 14:48 · maptiler-basic](session-trace/20261029-144810/report.md) | maptiler-basic | gl7-performance-optimization, main, main--mlt-1-3-0 | MLT 0.87×, MLT tessellated 0.42× | [flame](session-trace/20261029-144810/flame.html) |
| [2026-10-28 14:30 · osm-bright](session-trace/20261028-143057/report.md) | osm-bright (recorded: maptiler-basic) | gl1-mlt-facade-v2, gl2-dispatch, gl3-populate-pipeline, gl4-fill-bucket, gl5-line-bucket, gl6-symbol-bucket, gl7-before-splits, gl7-performance-optimization, main | MLT 0.76×, MLT tessellated 0.69× | [flame](session-trace/20261028-143057/flame.html) |
| [2026-10-28 08:57 · osm-bright](session-trace/20261028-085720/report.md) | osm-bright (recorded: maptiler-basic) | gl7-before-splits, gl7-performance-optimization | MLT 0.88×, MLT tessellated 0.77× | [flame](session-trace/20261028-085720/flame.html) |
| [2026-10-28 07:56 · osm-bright](session-trace/20261028-075655-osm-bright/report.md) | osm-bright (recorded: maptiler-basic) | – | MLT 0.90×, MLT tessellated 0.78× | [flame](session-trace/20261028-075655-osm-bright/flame.html) |
| [2026-10-28 07:29 · maptiler-basic](session-trace/20261028-072929-maptiler-basic/report.md) | maptiler-basic | – | MLT 0.85×, MLT tessellated 0.81× | [flame](session-trace/20261028-072929-maptiler-basic/flame.html) |
| [2026-10-27 15:18 · splits](session-trace/20261027-151854-splits/report.md) | maptiler-basic | gl7-before-splits, gl7-performance-optimization | – | [flame](session-trace/20261027-151854-splits/flame.html) |
| [2026-10-27 14:51 · maptiler-basic](session-trace/20261027-145149/report.md) | maptiler-basic | – | MLT 0.84×, MLT tessellated 0.76× | [flame](session-trace/20261027-145149/flame.html) |
| [2026-10-27 14:31 · maptiler-basic](session-trace/20261027-143159/report.md) | maptiler-basic | – | MLT 1.04×, MLT tessellated 0.84× | [flame](session-trace/20261027-143159/flame.html) |
| [2026-10-27 14:22 · maptiler-basic](session-trace/20261027-142219/report.md) | maptiler-basic | – | MLT 1.12×, MLT tessellated 0.75× | [flame](session-trace/20261027-142219/flame.html) |
| [2026-10-27 08:14 · maptiler-basic](session-trace/20261027-081430/report.md) | maptiler-basic | – | MLT 0.83×, MLT tessellated 0.68× | [flame](session-trace/20261027-081430/flame.html) |
| [2026-10-27 06:46 · maptiler-basic](session-trace/20261027-064651/report.md) | maptiler-basic | gl3-populate-pipeline, gl4-fill-bucket | MLT 0.90×, MLT tessellated 0.88× | [flame](session-trace/20261027-064651/flame.html) |
| [2026-10-23 11:09 · positron](session-trace/20261023-110933-positron/report.md) | positron (recorded: maptiler-basic) | – | MLT 0.90×, MLT tessellated 0.83× | [flame](session-trace/20261023-110933-positron/flame.html) |
| [2026-10-23 09:08 · maptiler-basic](session-trace/20261023-090811/report.md) | maptiler-basic | main | MLT 0.81×, MLT tessellated 0.74× | [flame](session-trace/20261023-090811/flame.html) |
| [2026-10-23 07:42 · maptiler-basic](session-trace/20261023-074205/report.md) | maptiler-basic | main | MLT 0.64×, MLT tessellated 0.54× | [flame](session-trace/20261023-074205/flame.html) |
| [2026-10-23 06:59 · maptiler-basic](session-trace/20261023-065948/report.md) | maptiler-basic | gl7-performance-optimization, main | MLT 1.04×, MLT tessellated 0.90× | [flame](session-trace/20261023-065948/flame.html) |
| [2026-10-22 15:32 · kernel-coverage](session-trace/20261022-153226/report.md) | kernel-coverage (recorded: maptiler-basic) | – | MLT 0.81×, MLT tessellated 0.50× | [flame](session-trace/20261022-153226/flame.html) |
| [2026-10-22 14:49 · maptiler-basic](session-trace/20261022-144914/report.md) | maptiler-basic | – | MLT 0.94×, MLT tessellated 0.65× | [flame](session-trace/20261022-144914/flame.html) |
| [2026-10-22 14:40 · maptiler-basic](session-trace/20261022-144000/report.md) | maptiler-basic | – | MLT 1.13×, MLT tessellated 0.64× | [flame](session-trace/20261022-144000/flame.html) |
| [2026-10-22 14:11 · e2e](session-trace/20261022-141122-e2e/report.md) | osm-bright | – | MLT 0.72×, MLT tessellated 0.61× | [flame](session-trace/20261022-141122-e2e/flame.html) |
| [2026-10-22 13:53 · maptiler-basic](session-trace/20261022-135340/report.md) | maptiler-basic | – | MLT 0.93×, MLT tessellated 0.66× | [flame](session-trace/20261022-135340/flame.html) |
| [2026-10-22 12:02 · osm-bright](session-trace/20261022-120230/report.md) | osm-bright | – | MLT 0.97×, MLT tessellated 0.88× | [flame](session-trace/20261022-120230/flame.html) |
| [2026-10-22 10:16 · maptiler-basic](session-trace/20261022-101613/report.md) | maptiler-basic | – | MLT 0.85×, MLT tessellated 0.72× | [flame](session-trace/20261022-101613/flame.html) |
| [2026-10-22 09:53 · earcut-path](session-trace/20261022-095301-earcut-path/report.md) | osm-bright | – | MLT 1.00× | [flame](session-trace/20261022-095301-earcut-path/flame.html) |
| [2026-10-22 08:30 · osm-bright](session-trace/20261022-083025/report.md) | osm-bright | – | MLT 1.02×, MLT tessellated 0.72× | [flame](session-trace/20261022-083025/flame.html) |
| [2026-10-22 07:21 · e2e](session-trace/20261022-072145-e2e/report.md) | osm-bright | – | MLT 0.75×, MLT tessellated 0.66× | [flame](session-trace/20261022-072145-e2e/flame.html) |
| [2026-10-21 16:49 · probe-idle-pcores](session-trace/20261021-164917-probe-idle-pcores/report.md) | osm-bright | – | MLT 1.00× | [flame](session-trace/20261021-164917-probe-idle-pcores/flame.html) |
| [2026-10-21 16:43 · probe-loaded](session-trace/20261021-164359-probe-loaded/report.md) | osm-bright | – | MLT 1.00× | [flame](session-trace/20261021-164359-probe-loaded/flame.html) |
| [2026-10-21 16:30 · probe-idle](session-trace/20261021-163036-probe-idle/report.md) | osm-bright | – | MLT 1.00× | [flame](session-trace/20261021-163036-probe-idle/flame.html) |
| [2026-10-21 15:36 · maptiler-basic](session-trace/20261021-153607/report.md) | maptiler-basic | gl1-mlt-facade-v2, gl2-dispatch, gl3-populate-pipeline, gl4-fill-bucket, gl5-line-bucket, gl6-symbol-bucket, gl7-performance-optimization | MLT 0.63×, MLT tessellated 0.53× | [flame](session-trace/20261021-153607/flame.html) |
| [2026-10-21 14:45 · builds-check](session-trace/20261021-144539-builds-check/report.md) | osm-bright | gl7-performance-optimization, main | – | [flame](session-trace/20261021-144539-builds-check/flame.html) |
| [2026-10-19 15:50 · maptiler-basic](session-trace/20261019-155038/report.md) | maptiler-basic | – | MLT 0.86×, MLT tessellated 0.75× | [flame](session-trace/20261019-155038/flame.html) |
| [2026-10-19 15:32 · maptiler-basic](session-trace/20261019-153249/report.md) | maptiler-basic | – | MLT 1.00×, MLT tessellated 0.68× | [flame](session-trace/20261019-153249/flame.html) |
| [2026-10-19 14:23 · maptiler-basic](session-trace/20261019-142304/report.md) | maptiler-basic | – | MLT 1.03×, MLT tessellated 0.74× | [flame](session-trace/20261019-142304/flame.html) |
| [2026-10-19 12:42 · maptiler-basic](session-trace/20261019-124231/report.md) | maptiler-basic | – | MLT 0.97×, MLT tessellated 0.72× | [flame](session-trace/20261019-124231/flame.html) |
