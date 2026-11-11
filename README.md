# Columnar MLT in MapLibre: the published docs

What the thesis changes in `@maplibre/mlt` and MapLibre GL JS, for MapLibre maintainers. Two MkDocs sites,
published together at <https://salkin975.github.io/Thesis-docs/>:

| Site | Source | Config | Published at |
|---|---|---|---|
| The changes, one page per change, with the benchmark reports | `changes/` | `mkdocs.public.yml` | `/` |
| The overview: the architecture in a few pages | `overview/` | `mkdocs.overview.yml` | `/overview/` |

The proposals themselves are the upstream issues
[maplibre/maplibre-tile-spec#2010](https://github.com/maplibre/maplibre-tile-spec/issues/2010) and
[maplibre/maplibre-gl-js#8985](https://github.com/maplibre/maplibre-gl-js/issues/8985).

## Preview

```sh
pip install -r requirements.txt
mkdocs serve -f mkdocs.public.yml
mkdocs serve -f mkdocs.overview.yml -a 127.0.0.1:8001
```

Links between the two sites stay relative in the sources; in a build, `hooks/site_links.py` points them at the
published pages.
