# Local generation tools

`render_motion.py PATTERN OUTPUT --input INPUT.json [--prefix PREFIX] [--preview FILE]`
assembles one typed motion instance. Use `--example` instead of `--input` only for an
explicitly illustrative demo. The output is a copy-ready macro fragment; the optional
preview adds document-level wrappers that must not be pasted into an HTML macro.

`build_gallery.py [--output DIRECTORY]` renders every implemented example with the same
renderer, checks each fragment and generates a standalone search/filter gallery,
individual previews, macro fragments, input JSON files and a byte-size manifest.

`validate_html_macro.py FILE` lints rendered fragments, including multiple combined
blocks: duplicate IDs/prefixes/keyframes, unscoped CSS, undefined animation names,
broken ID references, unresolved tokens, external runtime resources, unsafe tags or
event attributes, and required reduced-motion/print fallbacks. This is not a sanitizer.

`render_template.py TEMPLATE OUTPUT --prefix PREFIX --set KEY=value` remains an escaped
text-template helper for ordinary templates. v0.2 scene sources require typed input via
render_motion.py; the legacy command fails with migration guidance rather than silently
relabeling fixed numerical geometry. Do not use --allow-unresolved output for publishing.

Generation requires Python 3.10+ and no third-party packages. Catalog is serialized as
JSON-compatible YAML (YAML 1.2 subset), so standard-library json.load can read it.
No generation command logs into GitHub or Confluence or performs a remote write.
