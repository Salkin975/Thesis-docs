"""Points links between the two sites at the published pages.

The explainer pages (changes/, mkdocs.public.yml) and the overview (overview/,
mkdocs.overview.yml) are two MkDocs sites published together. Their sources link
to each other relatively, so the links work on GitHub and in an editor. In a
build, a link that leaves docs_dir and lands in the other site becomes a link to
that page of the published site (`extra.sites` in the config). Any other link
that leaves docs_dir is reported as a warning, which fails a strict build.
"""

import logging
import posixpath
import re
from pathlib import Path

log = logging.getLogger("mkdocs.hooks.site_links")

LINK = re.compile(r"\]\((?!https?:|mailto:|#)([^)\s]+)\)")
FENCE = re.compile(r"^(```|~~~).*?^\1", re.MULTILINE | re.DOTALL)

_docs_prefix = ""
_sites: dict[str, str] = {}


def on_config(config):
    global _docs_prefix, _sites
    root = Path(config.config_file_path).resolve().parent
    _docs_prefix = Path(config.docs_dir).resolve().relative_to(root).as_posix()
    _sites = {name: url.rstrip("/") + "/" for name, url in config.extra.get("sites", {}).items()}
    return config


def _page_url(path: str) -> str:
    """The URL of a source file relative to its site's root, with directory URLs."""
    if path == "index.md" or path.endswith("/index.md"):
        return path[: -len("index.md")]
    if path.endswith(".md"):
        return path[: -len(".md")] + "/"
    return path


def _rewrite(match, page) -> str:
    target = match.group(1)
    path, sep, anchor = target.partition("#")
    page_dir = posixpath.dirname(page.file.src_uri)
    resolved = posixpath.normpath(posixpath.join(_docs_prefix, page_dir, path))
    if resolved == _docs_prefix or resolved.startswith(_docs_prefix + "/"):
        return match.group(0)
    for name, url in _sites.items():
        if name != _docs_prefix and resolved.startswith(name + "/"):
            return f"]({url}{_page_url(resolved[len(name) + 1:])}{sep}{anchor})"
    log.warning("%s links to '%s', which is in neither site", page.file.src_uri, target)
    return match.group(0)


def on_page_markdown(markdown, page, config, files):
    def convert(text: str) -> str:
        return LINK.sub(lambda m: _rewrite(m, page), text)

    # Leave code fences untouched.
    out, last = [], 0
    for fence in FENCE.finditer(markdown):
        out.append(convert(markdown[last:fence.start()]))
        out.append(fence.group(0))
        last = fence.end()
    out.append(convert(markdown[last:]))
    return "".join(out)
